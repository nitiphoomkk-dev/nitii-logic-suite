"""One-time migration never overwrites unrecognized local customizations."""
import hashlib
import importlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.p = importlib.import_module('enable_auto_update')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / '.agents/skills/nitii-knowledge'
        self.scripts = self.skill / 'scripts'
        self.scripts.mkdir(parents=True)
        self.original = b'# approved original updater\n'
        (self.scripts / 'update_knowledge.py').write_bytes(self.original)
        for name in ('search_knowledge.py', 'read_knowledge.py'):
            (self.scripts / name).write_text('from update_knowledge import resolve\nroot = resolve(root)\n')
        (self.skill / 'SKILL.md').write_text('---\nname: nitii-knowledge\n---\n\n' + self.p.OLD_PARAGRAPH + '\n', encoding='utf-8')
        self.allowed = patch.object(self.p, 'SUPPORTED_UPDATERS', {hashlib.sha256(self.original).hexdigest()})
        self.allowed.start()
        self.addCleanup(self.allowed.stop)

    def test_patch_backups_original_and_preserves_other_files(self):
        (self.skill / 'personal.md').write_text('keep')
        result = self.p.apply_patch(self.root)
        self.assertEqual(result['status'], 'patched')
        self.assertEqual((self.scripts / 'update_knowledge.py').read_bytes(), self.p.payload())
        backup = Path(result['backup'])
        self.assertEqual((backup / '0.original').read_bytes(), self.original)
        self.assertEqual((self.skill / 'personal.md').read_text(), 'keep')
        self.assertIn(self.p.NEW_PARAGRAPH, (self.skill / 'SKILL.md').read_text(encoding='utf-8'))

    def test_second_apply_is_noop(self):
        self.p.apply_patch(self.root)
        self.assertEqual(self.p.apply_patch(self.root)['status'], 'already_patched')

    def test_unknown_customized_updater_is_rejected_without_any_write(self):
        (self.scripts / 'update_knowledge.py').write_text('# my customization')
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaises(ValueError):
            self.p.apply_patch(self.root)
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_dry_run_does_not_write(self):
        result = self.p.apply_patch(self.root, dry_run=True)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual((self.scripts / 'update_knowledge.py').read_bytes(), self.original)
        self.assertFalse(list(self.root.glob('.nitii-auto-update-backup-*')))

    def test_restore_returns_original_bytes(self):
        result = self.p.apply_patch(self.root)
        self.p.restore(Path(result['backup']))
        self.assertEqual((self.scripts / 'update_knowledge.py').read_bytes(), self.original)
        self.assertIn(self.p.OLD_PARAGRAPH, (self.skill / 'SKILL.md').read_text(encoding='utf-8'))

    def test_restore_refuses_to_overwrite_edits_after_patch(self):
        result = self.p.apply_patch(self.root)
        (self.scripts / 'update_knowledge.py').write_text('# later edit')
        with self.assertRaises(ValueError):
            self.p.restore(Path(result['backup']))
        self.assertEqual((self.scripts / 'update_knowledge.py').read_text(), '# later edit')

    def test_restore_write_failure_rolls_back_and_can_be_retried(self):
        result = self.p.apply_patch(self.root)
        real_write = self.p.atomic_write
        calls = []
        def fail_second(path, data):
            calls.append(path)
            if len(calls) == 2:
                raise OSError('write failed')
            return real_write(path, data)
        with patch.object(self.p, 'atomic_write', side_effect=fail_second):
            with self.assertRaises(OSError):
                self.p.restore(Path(result['backup']))
        self.assertEqual((self.scripts / 'update_knowledge.py').read_bytes(), self.p.payload())
        self.assertEqual(self.p.restore(Path(result['backup']))['status'], 'restored')

    def test_target_without_installed_reader_is_rejected(self):
        (self.scripts / 'read_knowledge.py').unlink()
        with self.assertRaises(ValueError):
            self.p.apply_patch(self.root)

    def test_no_installation_is_rejected(self):
        with self.assertRaises(ValueError):
            self.p.apply_patch(self.root / 'missing')

    def test_all_installed_copies_are_preflighted_before_changes(self):
        other = self.root / '.claude/skills/nitii-knowledge/scripts'
        other.mkdir(parents=True)
        (other / 'update_knowledge.py').write_text('# customized')
        with self.assertRaises(ValueError):
            self.p.apply_patch(self.root)
        self.assertEqual((self.scripts / 'update_knowledge.py').read_bytes(), self.original)


if __name__ == '__main__':
    unittest.main()
