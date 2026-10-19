"""Behavior tests: real ZIPs/files/hashes; only public HTTP I/O is replaced."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

try:
    import update_knowledge as u
except ModuleNotFoundError:
    u = None

BASE = 'https://raw.githubusercontent.com/nitiphoomkk-dev/nitii-logic-suite/knowledge/'
DOC = '00000000-0000-4000-8000-000000000001'


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixture(text='ไทย\r\n# data only\n', mutate=None, extra=None, missing=None,
            duplicate=None, symlink=None, pointer_change=None):
    sid = sha(text.encode())
    body = text.encode('utf-8')
    files = {'snapshot.json': encoded({'snapshotId': sid, 'documentCount': 1}),
             'INDEX.md': b'# Index\n', 'pages/' + DOC + '.md': body,
             'web/NAYOO_WIKI_01.txt': body}
    manifest = {'schemaVersion': 'nitii-wiki-snapshot.v1', 'snapshotId': sid,
                'documentCount': 1, 'documents': [
                    {'id': DOC, 'title': 'fixture', 'url': 'https://wiki.infonayoo.co/doc/example',
                     'collection': 'solution', 'revision': 1,
                     'updatedAt': '2026-10-19T00:00:00Z',
                     'checkedAtUtc': '2026-10-19T00:01:00Z',
                     'bodyPath': 'pages/' + DOC + '.md', 'bodyBytes': len(body),
                     'bodySha256': sha(body)}],
                'files': [{'path': path, 'bytes': len(data), 'sha256': sha(data)}
                          for path, data in sorted(files.items())]}
    if mutate:
        mutate(manifest, files)
    manifest_bytes = encoded(manifest)
    files['manifest.json'] = manifest_bytes
    if extra:
        files.update(extra)
    if missing:
        files.pop(missing, None)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path, data in files.items():
            archive.writestr(path, data)
        if duplicate:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                archive.writestr(duplicate, b'duplicate')
        if symlink:
            info = zipfile.ZipInfo(symlink)
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, b'../../outside')
    archive_bytes = stream.getvalue()
    pointer = {'schemaVersion': 'nitii-feed.v1', 'snapshotId': sid,
               'manifestPath': f'snapshots/{sid}/manifest.json',
               'manifestSha256': sha(manifest_bytes),
               'archivePath': f'snapshots/{sid}/knowledge.zip',
               'archiveSha256': sha(archive_bytes),
               'checkedAtUtc': '2026-10-19T13:00:00Z',
               'syncedAtUtc': '2026-10-19T13:00:00Z', 'documentCount': 1}
    if pointer_change:
        pointer_change(pointer)
    responses = {BASE + 'latest.json': encoded(pointer),
                 BASE + f'snapshots/{sid}/manifest.json': manifest_bytes,
                 BASE + f'snapshots/{sid}/knowledge.zip': archive_bytes}
    return pointer, responses


class Fetch:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, url, max_bytes):
        self.calls.append((url, max_bytes))
        value = self.responses[url]
        if isinstance(value, Exception):
            raise value
        return value  # Deliberately do not enforce bounds: the client must too.


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(u, 'data-only updater implementation is missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name) / 'cache'

    def install(self, text='old'):
        pointer, responses = fixture(text)
        result = u.update(self.cache, Fetch(responses))
        self.assertEqual(result['status'], 'updated')
        return pointer

    def assert_rejected_preserving_current(self, responses):
        before = (self.cache / 'CURRENT.json').read_bytes()
        result = u.update(self.cache, Fetch(responses))
        self.assertEqual(result['status'], 'stale', result)
        self.assertTrue(result['stale'])
        self.assertEqual((self.cache / 'CURRENT.json').read_bytes(), before)
        self.assertIsNotNone(u.resolve_cached(self.cache))

    def test_valid_data_becomes_complete_version_before_current_switch(self):
        pointer, responses = fixture()
        result = u.update(self.cache, Fetch(responses))
        self.assertEqual(result['status'], 'updated')
        root = self.cache / pointer['snapshotId']
        self.assertEqual(json.loads((self.cache / 'CURRENT.json').read_bytes()),
                         {'snapshotId': pointer['snapshotId'], 'root': pointer['snapshotId']})
        self.assertEqual((root / 'pages' / (DOC + '.md')).read_bytes(),
                         'ไทย\r\n# data only\n'.encode())
        self.assertEqual(u.resolve_cached(self.cache), root)

    def test_existing_version_is_immutable_and_corruption_is_rejected(self):
        pointer = self.install('same')
        root = self.cache / pointer['snapshotId']
        body = root / 'pages' / (DOC + '.md')
        original_stat = body.stat().st_mtime_ns
        _, responses = fixture('same')
        self.assertEqual(u.update(self.cache, Fetch(responses))['status'], 'current')
        self.assertEqual(body.stat().st_mtime_ns, original_stat)
        body.write_bytes(b'tampered')
        before = (self.cache / 'CURRENT.json').read_bytes()
        self.assertIsNone(u.resolve_cached(self.cache))
        self.assertNotEqual(u.update(self.cache, Fetch(responses))['status'], 'updated')
        self.assertEqual(body.read_bytes(), b'tampered')
        self.assertEqual((self.cache / 'CURRENT.json').read_bytes(), before)

    def test_check_only_fetches_pointer_and_never_publishes_cache(self):
        pointer, responses = fixture()
        fetch = Fetch({BASE + 'latest.json': responses[BASE + 'latest.json']})
        result = u.update(self.cache, fetch, check_only=True)
        self.assertEqual(result['status'], 'available')
        self.assertEqual(result['snapshotId'], pointer['snapshotId'])
        self.assertFalse((self.cache / 'CURRENT.json').exists())
        self.assertEqual([url for url, _ in fetch.calls], [BASE + 'latest.json'])

    def test_same_snapshot_pointer_cannot_lie_about_document_count(self):
        self.install('same')
        _, responses = fixture('same', pointer_change=lambda p: p.update(documentCount=2))
        self.assert_rejected_preserving_current(responses)

    def test_network_failure_keeps_previous_current_without_leaking_error_payload(self):
        self.install()
        marker = 'private-request-detail'
        before = (self.cache / 'CURRENT.json').read_bytes()
        result = u.update(self.cache, Fetch({BASE + 'latest.json': OSError(marker)}))
        self.assertEqual(result['status'], 'stale')
        self.assertNotIn(marker, json.dumps(result))
        self.assertEqual((self.cache / 'CURRENT.json').read_bytes(), before)

    def test_bad_pointer_schema_paths_hashes_and_counts_fail_closed(self):
        self.install()
        changes = [lambda p: p.update(schemaVersion='next.v9'),
                   lambda p: p.update(snapshotId='../escape'),
                   lambda p: p.update(manifestPath='https://evil.example/manifest.json'),
                   lambda p: p.update(archivePath='snapshots/elsewhere/knowledge.zip'),
                   lambda p: p.update(archiveSha256='0' * 64),
                   lambda p: p.update(manifestSha256='0' * 64),
                   lambda p: p.update(documentCount=5001)]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                _, responses = fixture('new', pointer_change=change)
                self.assert_rejected_preserving_current(responses)

    def test_zip_rejects_unlisted_executable_duplicate_link_and_traversal(self):
        self.install()
        variants = [dict(extra={'SKILL.md': b'instructions'}),
                    dict(extra={'pages/../../escape.md': b'escape'}),
                    dict(extra={'/absolute.txt': b'escape'}),
                    dict(extra={'pages\\evil.md': b'escape'}),
                    dict(extra={'web/C:evil.txt': b'escape'}),
                    dict(extra={'web/unlisted.txt': b'unlisted'}),
                    dict(duplicate='INDEX.md'), dict(symlink='web/link.txt'),
                    dict(missing='INDEX.md')]
        for variant in variants:
            with self.subTest(variant=variant):
                _, responses = fixture('new', **variant)
                self.assert_rejected_preserving_current(responses)
        self.assertFalse((self.cache.parent / 'escape.md').exists())

    def test_manifest_document_identity_counts_body_hash_and_bytes_are_validated(self):
        self.install()
        mutations = [lambda m, f: m.update(schemaVersion='unknown.v2'),
                     lambda m, f: m.update(snapshotId='1' * 64),
                     lambda m, f: m.update(documentCount=2),
                     lambda m, f: m['documents'][0].update(bodySha256='0' * 64),
                     lambda m, f: m['documents'][0].update(bodyBytes=999),
                     lambda m, f: m['documents'][0].update(bodyPath='pages/other.md'),
                     lambda m, f: m['documents'].append(copy.deepcopy(m['documents'][0])),
                     lambda m, f: m['files'][0].update(sha256='0' * 64)]
        for mutate in mutations:
            with self.subTest(mutation=mutations.index(mutate)):
                _, responses = fixture('new', mutate=mutate)
                self.assert_rejected_preserving_current(responses)

    def test_detached_manifest_must_match_manifest_inside_archive(self):
        self.install()
        pointer, responses = fixture('new')
        path = BASE + pointer['manifestPath']
        changed = json.loads(responses[path]); changed['inventoryFingerprint'] = 'changed'
        responses[path] = encoded(changed)
        pointer['manifestSha256'] = sha(responses[path])
        responses[BASE + 'latest.json'] = encoded(pointer)
        self.assert_rejected_preserving_current(responses)

    def test_bounded_fetch_and_expanded_size_are_enforced_even_with_fake_fetch(self):
        self.install()
        _, responses = fixture('new')
        before = (self.cache / 'CURRENT.json').read_bytes()
        for name in ['MAX_ARCHIVE', 'MAX_EXPANDED', 'MAX_METADATA']:
            with self.subTest(limit=name), patch.object(u, name, 64):
                result = u.update(self.cache, Fetch(responses))
                self.assertIn(result['status'], ('stale', 'error'))
                self.assertTrue(result['stale'])
                self.assertEqual((self.cache / 'CURRENT.json').read_bytes(), before)
            # The synthetic lower limit may also disqualify the old snapshot;
            # after restoring production limits the untouched reader must work.
            self.assertIsNotNone(u.resolve_cached(self.cache))

    def test_current_path_traversal_and_extra_cached_files_do_not_resolve(self):
        pointer = self.install()
        current = self.cache / 'CURRENT.json'
        valid = current.read_bytes()
        for root in ['../outside', '/outside', pointer['snapshotId'] + '/pages']:
            current.write_bytes(encoded({'snapshotId': pointer['snapshotId'], 'root': root}))
            self.assertIsNone(u.resolve_cached(self.cache))
        current.write_bytes(valid)
        (self.cache / pointer['snapshotId'] / 'SKILL.md').write_text('unexpected')
        self.assertIsNone(u.resolve_cached(self.cache))

    def test_failure_during_atomic_current_replace_keeps_previous_reader(self):
        old = self.install('old')
        _, responses = fixture('new')
        real_replace = os.replace
        def failing_replace(src, dst):
            if Path(dst).name == 'CURRENT.json':
                raise OSError('simulated interrupted publication')
            return real_replace(src, dst)
        with patch.object(u.os, 'replace', side_effect=failing_replace):
            self.assert_rejected_preserving_current(responses)
        self.assertEqual(u.resolve_cached(self.cache).name, old['snapshotId'])

    def test_markdown_is_only_data_and_recognizable_credentials_are_rejected(self):
        marker = Path(self.temp.name) / 'executed'
        text = f'import pathlib; pathlib.Path({str(marker)!r}).touch()\n'
        _, responses = fixture(text)
        self.assertEqual(u.update(self.cache, Fetch(responses))['status'], 'updated')
        self.assertFalse(marker.exists())
        _, responses = fixture('ol_api_' + 'a' * 38)
        self.assert_rejected_preserving_current(responses)

    def test_https_allowlist_and_redirect_policy_are_strict(self):
        allowed = BASE + 'latest.json'
        self.assertEqual(u.validate_url(allowed), allowed)
        for url in [allowed.replace('https:', 'http:'),
                    allowed.replace('raw.githubusercontent.com', 'evil.example'),
                    allowed.replace('/knowledge/', '/main/'),
                    allowed + '?token=x', allowed + '#fragment',
                    allowed.replace('raw.githubusercontent.com', 'user@raw.githubusercontent.com'),
                    BASE + '../main/file', BASE + '%2e%2e/main/file']:
            with self.subTest(url=url), self.assertRaises(u.UpdateError):
                u.validate_url(url)
        handler = u.SafeRedirect()
        from urllib.request import Request
        with self.assertRaises(u.UpdateError):
            handler.redirect_request(Request(allowed), None, 302, 'Found', {},
                                     'https://example.com/escape')

    def test_resolve_falls_back_to_original_bundle_when_cache_is_invalid(self):
        bundled = Path(self.temp.name) / 'bundled'
        bundled.mkdir()
        with patch.dict(os.environ, {'NITII_CACHE': str(self.cache)}):
            self.assertEqual(u.resolve(bundled), bundled)
            pointer = self.install()
            self.assertEqual(u.resolve(bundled), self.cache / pointer['snapshotId'])

    def test_knowledge_cache_override_is_used_by_readers(self):
        bundled = Path(self.temp.name) / 'bundled'
        pointer = self.install()
        with patch.dict(os.environ, {'NITII_KNOWLEDGE_CACHE': str(self.cache),
                                     'NITII_CACHE': str(self.cache / 'unrelated')}):
            self.assertEqual(u.resolve(bundled), self.cache / pointer['snapshotId'])

    def test_empty_page_is_valid_and_snapshot_metadata_must_agree(self):
        self.install('')
        def change_snapshot(manifest, files):
            files['snapshot.json'] = encoded({'snapshotId': manifest['snapshotId'],
                                             'documentCount': 2})
            record = next(r for r in manifest['files'] if r['path'] == 'snapshot.json')
            record.update(bytes=len(files['snapshot.json']), sha256=sha(files['snapshot.json']))
        _, responses = fixture('new', mutate=change_snapshot)
        self.assert_rejected_preserving_current(responses)

    def test_bootstrap_null_read_time_stays_stale_and_is_not_a_live_read(self):
        pointer, responses = fixture(pointer_change=lambda p: p.update(
            bootstrap=True, checkedAtUtc=None))
        result = u.update(self.cache, Fetch(responses))
        self.assertEqual(result['status'], 'updated')
        self.assertTrue(result['bootstrap'])
        self.assertTrue(result['stale'])
        self.assertIsNone(result['checkedAtUtc'])
        self.assertEqual(result['syncedAtUtc'], '2026-10-19T13:00:00Z')
        result = u.update(self.cache, Fetch(responses), check_only=True)
        self.assertEqual(result['status'], 'current')
        self.assertTrue(result['stale'])
        self.assertTrue(result['bootstrap'])
        _, bad = fixture('next', pointer_change=lambda p: p.update(checkedAtUtc=None))
        self.assert_rejected_preserving_current(bad)

    def test_deeply_malformed_current_falls_back_instead_of_crashing_reader(self):
        self.cache.mkdir()
        depth = sys.getrecursionlimit() + 100
        (self.cache / 'CURRENT.json').write_bytes(b'{"bad":' + b'[' * depth + b'0' + b']' * depth + b'}')
        self.assertIsNone(u.resolve_cached(self.cache))

    def test_public_archive_validator_returns_verified_data_only(self):
        pointer, responses = fixture()
        self.assertTrue(callable(getattr(u, 'validate_snapshot_archive', None)),
                        'public archive validator is missing')
        data = u.validate_snapshot_archive(responses[BASE + pointer['archivePath']],
                                           responses[BASE + pointer['manifestPath']],
                                           pointer['snapshotId'])
        self.assertEqual(data['pages/' + DOC + '.md'], 'ไทย\r\n# data only\n'.encode())

    def test_cli_exposes_cache_and_check_without_executing_network_for_help(self):
        result = subprocess.run([sys.executable, str(Path(u.__file__)), '--help'],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn('--cache', result.stdout)
        self.assertIn('--check', result.stdout)


if __name__ == '__main__':
    unittest.main()
