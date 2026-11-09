"""The distributed ZIP must contain the same verified payload as the installer."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile
import build_auto_update_patch as build
import enable_auto_update as patch


class DistributionTests(unittest.TestCase):
    def test_release_zip_has_verified_payload_installer_and_instructions(self):
        with tempfile.TemporaryDirectory() as temp:
            output = build.build(Path(temp))
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {
                    'enable_auto_update.py', 'update_knowledge.py',
                    'AUTO_UPDATE_PATCH_TH.md', 'SHA256SUMS.txt'})
                self.assertEqual(archive.read('update_knowledge.py'), patch.payload())
                for line in archive.read('SHA256SUMS.txt').decode().splitlines():
                    digest, name = line.split('  ', 1)
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
