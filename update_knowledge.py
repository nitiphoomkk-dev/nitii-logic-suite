#!/usr/bin/env python3
"""Download validated public data snapshots; never install or execute code.

Only CURRENT.json is replaced. Snapshot directories are immutable. A failed
update reports stale data and leaves the previous reader pointer untouched.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Callable
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import uuid
import zipfile

BASE = 'https://raw.githubusercontent.com/nitiphoomkk-dev/nitii-logic-suite/knowledge/'
PREFIX = '/nitiphoomkk-dev/nitii-logic-suite/knowledge/'
MAX_ARCHIVE = 100 * 1024 * 1024
MAX_EXPANDED = 150 * 1024 * 1024
MAX_METADATA = 16 * 1024 * 1024
MAX_DOCUMENTS = 5000
HEX = re.compile(r'[0-9a-f]{64}\Z')
PAGE = re.compile(r'pages/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\.md\Z')
WEB = re.compile(r'web/[A-Za-z0-9_.-]+\.txt\Z')
CREDENTIAL = re.compile(
    rb'(?:ol_api_[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|'
    rb'github_pat_[A-Za-z0-9_]{20,}|sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}|'
    rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')


class UpdateError(ValueError):
    """A safe error message that never contains source text or credentials."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UpdateError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'Duplicate JSON field')
        result[key] = value
    return result


def _json(data: bytes) -> dict:
    _require(len(data) <= MAX_METADATA, 'Metadata response exceeds limit')
    try:
        value = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise UpdateError('Invalid UTF-8 JSON') from exc
    _require(isinstance(value, dict), 'Expected JSON object')
    return value


def _digest(value) -> bool:
    return isinstance(value, str) and HEX.fullmatch(value) is not None


def _count(value, maximum=MAX_DOCUMENTS, minimum=1) -> bool:
    return type(value) is int and minimum <= value <= maximum


def validate_url(url: str) -> str:
    """Allow HTTPS only on the public repository's exact knowledge branch."""
    _require(isinstance(url, str), 'Invalid feed URL')
    parsed = urlsplit(url)
    _require(parsed.scheme == 'https' and parsed.netloc == 'raw.githubusercontent.com',
             'Feed URL outside HTTPS host allowlist')
    _require(not parsed.query and not parsed.fragment and parsed.path.startswith(PREFIX),
             'Feed URL outside branch allowlist')
    _require('%' not in parsed.path and '\\' not in parsed.path and
             all(part not in ('.', '..', '') for part in parsed.path[1:].split('/')),
             'Non-canonical feed URL')
    return url


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download(url: str, max_bytes: int) -> bytes:
    validate_url(url)
    # No cookie jar, authentication handlers, environment proxy credentials or
    # caller-controlled headers. TLS certificate verification uses stdlib defaults.
    opener = build_opener(ProxyHandler({}), SafeRedirect())
    request = Request(url, headers={'User-Agent': 'nitii-logic-suite-data-updater/1.2'})
    with opener.open(request, timeout=30) as response:
        validate_url(response.geturl())
        length = response.headers.get('Content-Length')
        if length is not None:
            _require(length.isdigit() and int(length) <= max_bytes,
                     'Response exceeds download limit')
        data = response.read(max_bytes + 1)
    _require(len(data) <= max_bytes, 'Response exceeds download limit')
    return data


def _fetch(fetch, path: str, limit: int) -> bytes:
    url = validate_url(BASE + path)
    data = fetch(url, limit)
    _require(isinstance(data, bytes) and len(data) <= limit,
             'Invalid or oversized download')
    return data


def _utc(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.utcoffset() == timedelta(0)
    except ValueError:
        return False


def _pointer(data: bytes) -> dict:
    pointer = _json(data)
    _require(pointer.get('schemaVersion') == 'nitii-feed.v1', 'Unknown feed schema')
    sid = pointer.get('snapshotId')
    _require(_digest(sid), 'Invalid snapshot ID')
    _require(pointer.get('manifestPath') == f'snapshots/{sid}/manifest.json' and
             pointer.get('archivePath') == f'snapshots/{sid}/knowledge.zip',
             'Non-canonical snapshot paths')
    _require(_digest(pointer.get('manifestSha256')) and
             _digest(pointer.get('archiveSha256')), 'Invalid pointer hash')
    _require(_count(pointer.get('documentCount')), 'Invalid document count')
    bootstrap = pointer.get('bootstrap', False)
    _require(type(bootstrap) is bool, 'Invalid bootstrap status')
    checked = pointer.get('checkedAtUtc')
    _require((_utc(checked) or (bootstrap and checked is None)) and
             _utc(pointer.get('syncedAtUtc')),
             'Invalid feed timestamps')
    return pointer


def _allowed(path) -> bool:
    if not isinstance(path, str) or '\\' in path or ':' in path or '\x00' in path:
        return False
    if any(part in ('', '.', '..') for part in path.split('/')):
        return False
    name = path.rsplit('/', 1)[-1].split('.')[0].upper()
    if re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])', name):
        return False
    return path in ('manifest.json', 'snapshot.json', 'INDEX.md') or bool(
        PAGE.fullmatch(path) or WEB.fullmatch(path))


def _manifest(data: bytes, sid: str | None = None) -> tuple[dict, dict]:
    manifest = _json(data)
    _require(manifest.get('schemaVersion') == 'nitii-wiki-snapshot.v1',
             'Unknown manifest schema')
    _require(_digest(manifest.get('snapshotId')) and
             (sid is None or manifest['snapshotId'] == sid), 'Snapshot ID mismatch')
    docs = manifest.get('documents')
    _require(isinstance(docs, list) and _count(len(docs)) and
             manifest.get('documentCount') == len(docs) and
             type(manifest.get('documentCount')) is int, 'Manifest count mismatch')
    records = manifest.get('files')
    _require(isinstance(records, list), 'Missing snapshot file inventory')
    inventory = {}
    total = len(data)
    for record in records:
        _require(isinstance(record, dict), 'Invalid file inventory record')
        path = record.get('path')
        _require(_allowed(path) and path != 'manifest.json' and path not in inventory,
                 'Invalid or duplicate inventory path')
        _require(_digest(record.get('sha256')) and
                 _count(record.get('bytes'), MAX_EXPANDED, 0), 'Invalid file receipt')
        total += record['bytes']
        inventory[path] = record
    _require(total <= MAX_EXPANDED, 'Expanded snapshot exceeds limit')
    _require({'snapshot.json', 'INDEX.md'} <= inventory.keys(), 'Missing core data file')
    ids = set()
    pages = set()
    for doc in docs:
        _require(isinstance(doc, dict), 'Invalid document record')
        identifier = doc.get('id')
        try:
            canonical = str(uuid.UUID(identifier))
        except (ValueError, TypeError, AttributeError) as exc:
            raise UpdateError('Invalid document ID') from exc
        _require(identifier == canonical and identifier not in ids, 'Duplicate document ID')
        path = doc.get('bodyPath')
        _require(path == f'pages/{identifier}.md' and path in inventory,
                 'Invalid document body path')
        record = inventory[path]
        _require(_digest(doc.get('bodySha256')) and
                 doc['bodySha256'] == record['sha256'] and
                 _count(doc.get('bodyBytes'), MAX_EXPANDED, 0) and
                 doc['bodyBytes'] == record['bytes'], 'Document body receipt mismatch')
        ids.add(identifier)
        pages.add(path)
    _require(pages == {path for path in inventory if path.startswith('pages/')},
             'Unlisted or missing document page')
    return manifest, inventory


def _validate_files(files: dict[str, bytes], manifest_bytes: bytes,
                    sid: str | None = None) -> dict:
    manifest, inventory = _manifest(manifest_bytes, sid)
    _require(set(files) == set(inventory) | {'manifest.json'}, 'Snapshot file set mismatch')
    _require(files['manifest.json'] == manifest_bytes, 'Archive manifest mismatch')
    _require(sum(len(value) for value in files.values()) <= MAX_EXPANDED,
             'Expanded snapshot exceeds limit')
    for path, data in files.items():
        if path != 'manifest.json':
            record = inventory[path]
            _require(len(data) == record['bytes'] and _sha(data) == record['sha256'],
                     'Snapshot file hash or size mismatch')
        try:
            data.decode('utf-8')
        except UnicodeError as exc:
            raise UpdateError('Snapshot contains non-UTF-8 text') from exc
        _require(CREDENTIAL.search(data) is None, 'Recognizable credential in snapshot')
    snapshot = _json(files['snapshot.json'])
    _require(snapshot.get('snapshotId') == manifest['snapshotId'] and
             snapshot.get('documentCount') == manifest['documentCount'] and
             type(snapshot.get('documentCount')) is int, 'Snapshot metadata mismatch')
    if 'schemaVersion' in snapshot:
        _require(snapshot['schemaVersion'] == 'nitii-wiki-snapshot.v1',
                 'Unknown snapshot metadata schema')
    return manifest


def _archive(data: bytes, manifest_bytes: bytes, sid: str) -> dict[str, bytes]:
    _require(len(data) <= MAX_ARCHIVE, 'Archive exceeds compressed limit')
    files = {}
    total = 0
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            path = info.filename
            mode = info.external_attr >> 16
            _require(_allowed(path) and path not in files and not info.is_dir(),
                     'Disallowed or duplicate ZIP entry')
            _require(not stat.S_ISLNK(mode) and
                     (stat.S_IFMT(mode) in (0, stat.S_IFREG)) and
                     not info.flag_bits & 1, 'Unsupported ZIP entry type')
            _require(info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                     'Unsupported ZIP compression')
            total += info.file_size
            _require(total <= MAX_EXPANDED, 'Expanded snapshot exceeds limit')
            with archive.open(info) as source:
                body = source.read(info.file_size + 1)
            _require(len(body) == info.file_size, 'ZIP entry size mismatch')
            files[path] = body
    _validate_files(files, manifest_bytes, sid)
    return files


def validate_snapshot_archive(data: bytes, manifest_bytes: bytes,
                              sid: str) -> dict[str, bytes]:
    """Validate ZIP structure, exact inventory and all text/body hashes.

    A caller must separately authenticate the detached manifest/archive SHA-256
    from its trusted pointer; this function checks their internal consistency.
    """
    return _archive(data, manifest_bytes, sid)


def _read(path: Path, limit: int) -> bytes:
    _require(not path.is_symlink(), 'Symlink in cache')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    _require(len(data) <= limit, 'Cached file exceeds limit')
    return data


def _cached_root(root: Path, sid: str) -> dict:
    _require(root.is_dir() and not root.is_symlink(), 'Missing or linked snapshot root')
    manifest_bytes = _read(root / 'manifest.json', MAX_METADATA)
    manifest, inventory = _manifest(manifest_bytes, sid)
    actual = set()
    for path in root.rglob('*'):
        _require(not path.is_symlink(), 'Symlink in cache')
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            _require(relative in ('pages', 'web'), 'Unexpected cache directory')
        else:
            _require(path.is_file(), 'Unsupported cached file')
            actual.add(relative)
    _require(actual == set(inventory) | {'manifest.json'}, 'Cache file set mismatch')
    files = {'manifest.json': manifest_bytes}
    for path, record in inventory.items():
        files[path] = _read(root / path, record['bytes'])
    _validate_files(files, manifest_bytes, sid)
    return manifest


def default_cache() -> Path:
    default = str(Path.home() / '.cache' / 'nitii-logic-suite')
    return Path(os.environ.get('NITII_KNOWLEDGE_CACHE',
                               os.environ.get('NITII_CACHE', default))).expanduser()


def resolve_cached(cache: Path) -> Path | None:
    """Return a complete validated CURRENT root, or None; never change data."""
    try:
        cache = Path(cache).expanduser()
        current = _json(_read(cache / 'CURRENT.json', MAX_METADATA))
        sid = current.get('snapshotId')
        _require(set(current) == {'snapshotId', 'root'} and _digest(sid) and
                 current.get('root') == sid, 'Invalid CURRENT pointer')
        root = cache / sid
        _cached_root(root, sid)
        return root
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile):
        return None


def resolve(root: Path) -> Path:
    """Readers pass their original bundled knowledge root as the fallback."""
    return resolve_cached(default_cache()) or Path(root)


def _publish(cache: Path, sid: str, files: dict[str, bytes]) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / sid
    if target.exists() or target.is_symlink():
        _cached_root(target, sid)
        _require(_read(target / 'manifest.json', MAX_METADATA) == files['manifest.json'],
                 'Immutable snapshot already exists with different contents')
    else:
        with tempfile.TemporaryDirectory(prefix='.staging-', dir=cache) as temporary:
            staged = Path(temporary) / sid
            staged.mkdir()
            for name, data in files.items():
                destination = staged / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open('xb') as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            _cached_root(staged, sid)
            os.replace(staged, target)
    temporary_pointer = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', prefix='.CURRENT-', suffix='.tmp',
                                         dir=cache, delete=False) as stream:
            temporary_pointer = Path(stream.name)
            stream.write(json.dumps({'snapshotId': sid, 'root': sid},
                                    sort_keys=True).encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_pointer, cache / 'CURRENT.json')
    finally:
        if temporary_pointer is not None:
            temporary_pointer.unlink(missing_ok=True)
    return target


def update(cache: Path, fetch: Callable[[str, int], bytes] | None = None,
           check_only: bool = False) -> dict:
    """Update data or return a safe error; failures never advance CURRENT."""
    cache = Path(cache).expanduser()
    previous = resolve_cached(cache)
    try:
        fetch = fetch or _download
        pointer = _pointer(_fetch(fetch, 'latest.json', MAX_METADATA))
        sid = pointer['snapshotId']
        provenance = {'bootstrap': pointer.get('bootstrap', False),
                      'checkedAtUtc': pointer['checkedAtUtc'],
                      'syncedAtUtc': pointer['syncedAtUtc']}
        current = previous is not None and previous.name == sid and _sha(
            _read(previous / 'manifest.json', MAX_METADATA)) == pointer['manifestSha256']
        if current:
            _require(_json(_read(previous / 'manifest.json', MAX_METADATA))['documentCount'] ==
                     pointer['documentCount'], 'Pointer document count mismatch')
            return {'status': 'current', 'snapshotId': sid, 'root': str(previous),
                    'stale': provenance['bootstrap'], **provenance}
        if check_only:
            return {'status': 'available', 'snapshotId': sid,
                    'documentCount': pointer['documentCount'],
                    'stale': previous is not None or provenance['bootstrap'], **provenance}
        manifest_bytes = _fetch(fetch, pointer['manifestPath'], MAX_METADATA)
        _require(_sha(manifest_bytes) == pointer['manifestSha256'], 'Manifest SHA mismatch')
        manifest, _ = _manifest(manifest_bytes, sid)
        _require(manifest['documentCount'] == pointer['documentCount'],
                 'Pointer document count mismatch')
        archive_bytes = _fetch(fetch, pointer['archivePath'], MAX_ARCHIVE)
        _require(_sha(archive_bytes) == pointer['archiveSha256'], 'Archive SHA mismatch')
        files = validate_snapshot_archive(archive_bytes, manifest_bytes, sid)
        root = _publish(cache, sid, files)
        return {'status': 'updated', 'snapshotId': sid, 'root': str(root),
                'stale': provenance['bootstrap'], **provenance}
    except Exception as exc:
        # Network errors can contain user-controlled messages, URLs or headers.
        # Report only our sanitized validation errors or the exception class.
        error = str(exc) if isinstance(exc, UpdateError) else f'Update failed ({type(exc).__name__})'
        result = {'status': 'stale' if previous is not None else 'error',
                  'stale': True, 'error': error}
        if previous is not None:
            result.update(snapshotId=previous.name, root=str(previous))
        return result


def main(argv=None) -> int:
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=default_cache(),
                        help='versioned data cache (default: ~/.cache/nitii-logic-suite)')
    parser.add_argument('--check', action='store_true', help='check latest pointer only')
    args = parser.parse_args(argv)
    result = update(args.cache, check_only=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 1 if result['status'] in ('error', 'stale') else 0


if __name__ == '__main__':
    raise SystemExit(main())
