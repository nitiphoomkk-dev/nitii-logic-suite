#!/usr/bin/env python3
"""One-time, backed-up Nitii 1.2 patch. Python 3.9+, standard library only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid

VERSION = '1.2.1'
# Original released 1.2 updater and the maintained repository edition.
SUPPORTED_UPDATERS = {
    '8ea93965a445145f84c67f47488a662cf6a31aae1e38dfc8e221e3cd2487a3c9',
    'd2139b10c9dbb51c4960f2f63cd54957ea4a14e306efad929dfbd20150a3f9fb',
    'd2139b10c9dbb51c4960f2f63cd54957ea4a14e306efad929dfbd20150a3f9fb',
    'd2139b10c9dbb51c4960f2f63cd54957ea4a14e306efad929dfbd20150a3f9fb',
}
PAYLOAD_SHA256 = 'c71af66f7b6264d5cb6a91cd369f353c3cc3cdbb16259694180bc15da628f7bd'
OLD_PARAGRAPH = 'For current-policy work, run `python scripts/update_knowledge.py` once per session (network permission permitting). It checks the public feed and downloads only a new verified data snapshot; no Wiki key is needed by recipients. On failure disclose stale baseline/cache date; do not claim live freshness. Search/read helpers select the validated cache. Daily publisher target: 20:00 Asia/Bangkok; GitHub can delay. Installation alone does not update host-uploaded files.'
NEW_PARAGRAPH = 'Before-use automatic refresh (1.2.1): use the search/read helpers below; each helper checks the public feed before reading, downloads only a new verified data snapshot and selects the validated cache. Users do not run a separate update command. Read the knowledge_update JSON on stderr as well as the evidence JSON on stdout: retain checkedAtUtc/syncedAtUtc and disclose stale/bundle fallback on failure. On failure checkedAtUtc is unknown (null); report snapshotCapturedAtUtc as the copy date when available, never as a fresh Wiki check. This retrieves the latest published daily snapshot, not realtime Wiki. No recipient Wiki key is needed. Daily publisher target: 20:00 Asia/Bangkok; GitHub can delay. Without Python/network, disclose the bundled snapshot date; host-uploaded files do not update automatically.'
SKILL_LOCATIONS = (
    '.', 'nitii-knowledge', 'skills/nitii-knowledge',
    '.agents/skills/nitii-knowledge', '.claude/skills/nitii-knowledge',
    '.codex/skills/nitii-knowledge', 'modules/nitii-knowledge',
    'plugins/nitii-logic-suite/skills/nitii-knowledge',
    'nitii-logic-suite/plugins/nitii-logic-suite/skills/nitii-knowledge',
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def payload():
    data = Path(__file__).with_name('update_knowledge.py').read_bytes()
    if sha(data) != PAYLOAD_SHA256:
        raise ValueError('Patch payload hash mismatch; obtain the complete original patch ZIP')
    return data


def safe_path(root, relative):
    candidate = root / relative
    # Reject links/reparse targets rather than silently patching another install.
    for part in (candidate, *candidate.parents):
        if part == root.parent:
            break
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Linked installation paths are not supported')
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError('Patch path leaves the selected installation')
    return candidate


def atomic_write(path, data):
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.nitii-patch-', delete=False) as f:
            temp = Path(f.name)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def apply_patch(install_root, dry_run=False):
    root = Path(install_root).expanduser().absolute()
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Select the installed Nitii 1.2 skill, plugin, or project folder')
    new = payload()
    changes, seen = [], set()
    for location in SKILL_LOCATIONS:
        skill = safe_path(root, location)
        updater = safe_path(root, str((skill / 'scripts/update_knowledge.py').relative_to(root)))
        if not updater.is_file() or updater in seen:
            continue
        seen.add(updater)
        old = updater.read_bytes()
        if old != new and sha(old) not in SUPPORTED_UPDATERS:
            raise ValueError('Unrecognized/customized updater; no files were changed')
        for name in ('search_knowledge.py', 'read_knowledge.py'):
            reader = safe_path(root, str((skill / 'scripts' / name).relative_to(root)))
            if not reader.is_file() or 'from update_knowledge import resolve' not in reader.read_text(encoding='utf-8'):
                raise ValueError('Expected Nitii 1.2 search/read helpers were not found')
        if old != new:
            changes.append((updater, old, new))
        instruction = safe_path(root, str((skill / 'SKILL.md').relative_to(root)))
        text_bytes = instruction.read_bytes()
        text = text_bytes.decode('utf-8')
        if OLD_PARAGRAPH in text:
            changes.append((instruction, text_bytes, text.replace(OLD_PARAGRAPH, NEW_PARAGRAPH, 1).encode('utf-8')))
        elif NEW_PARAGRAPH not in text:
            raise ValueError('Knowledge skill instructions were customized; no files were changed')
    if not seen:
        raise ValueError('No supported Nitii 1.2 installation found; version 1.1 needs a one-time upgrade')
    if not changes:
        return {'status': 'already_patched', 'version': VERSION, 'installations': len(seen)}
    if dry_run:
        return {'status': 'ready', 'version': VERSION, 'files': len(changes), 'installations': len(seen)}
    backup = root / ('.nitii-auto-update-backup-' + uuid.uuid4().hex)
    backup.mkdir()
    records = []
    for i, (target, old, new_bytes) in enumerate(changes):
        (backup / f'{i}.original').write_bytes(old)
        records.append({'path': target.relative_to(root).as_posix(), 'backup': f'{i}.original',
                        'originalSha256': sha(old), 'patchedSha256': sha(new_bytes)})
    receipt = {'version': VERSION, 'root': str(root), 'createdAtUtc': datetime.now(timezone.utc).isoformat(),
               'files': records}
    (backup / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    written = []
    try:
        for target, old, new_bytes in changes:
            if target.read_bytes() != old:
                raise ValueError('Installation changed while patching')
            atomic_write(target, new_bytes)
            written.append((target, old))
    except Exception:
        for target, old in reversed(written):
            atomic_write(target, old)
        raise
    return {'status': 'patched', 'version': VERSION, 'files': len(changes),
            'installations': len(seen), 'backup': str(backup)}


def restore(backup):
    backup = Path(backup).absolute()
    record = json.loads((backup / 'receipt.json').read_text(encoding='utf-8'))
    root = backup.parent
    if Path(record['root']).resolve() != root.resolve():
        raise ValueError('Backup belongs to a different installation')
    changes = []
    for item in record['files']:
        target, original = safe_path(root, item['path']), safe_path(backup, item['backup'])
        data = original.read_bytes()
        if sha(data) != item['originalSha256'] or sha(target.read_bytes()) != item['patchedSha256']:
            raise ValueError('Backup or installed files changed; refusing to overwrite edits')
        changes.append((target, target.read_bytes(), data))
    written = []
    try:
        for target, before, data in changes:
            if target.read_bytes() != before:
                raise ValueError('Installation changed while restoring')
            atomic_write(target, data)
            written.append((target, before))
    except Exception:
        for target, before in reversed(written):
            atomic_write(target, before)
        raise
    return {'status': 'restored', 'files': len(changes)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--install-root', type=Path)
    group.add_argument('--restore', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        if args.restore:
            result = restore(args.restore)
        else:
            root = args.install_root or Path(input('Nitii installation/project folder: ').strip().strip('"'))
            result = apply_patch(root, args.dry_run)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({'status': 'error', 'error': str(error)}, ensure_ascii=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
