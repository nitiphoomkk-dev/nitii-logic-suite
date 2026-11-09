"""Before-use refresh behavior; real snapshots, only HTTP replaced."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import update_knowledge as u
from test_update_knowledge import fixture, Fetch


class AutoRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name) / 'cache'
        self.bundle = Path(self.temp.name) / 'bundle'
        self.bundle.mkdir()
        self.env = patch.dict(os.environ, {'NITII_KNOWLEDGE_CACHE': str(self.cache)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def resolve(self, fetch):
        err, out = io.StringIO(), io.StringIO()
        with patch.object(u, '_download', fetch), contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            root = u.resolve(self.bundle)
        self.assertEqual(out.getvalue(), '', 'refresh must not pollute reader JSON stdout')
        return root, json.loads(err.getvalue())

    def test_first_search_downloads_before_resolving(self):
        pointer, responses = fixture('fresh rule')
        fetch = Fetch(responses)
        root, status = self.resolve(fetch)
        self.assertEqual(root, self.cache / pointer['snapshotId'])
        self.assertEqual(status['knowledge_update']['status'], 'updated')
        self.assertEqual(len(fetch.calls), 3)

    def test_next_use_only_fetches_pointer_if_unchanged(self):
        _, responses = fixture('fresh rule')
        fetch = Fetch(responses)
        self.resolve(fetch)
        fetch.calls.clear()
        _, status = self.resolve(fetch)
        self.assertEqual(status['knowledge_update']['status'], 'current')
        self.assertEqual(len(fetch.calls), 1)

    def test_next_use_replaces_old_cache_with_new_verified_rule(self):
        _, old = fixture('old rule')
        self.resolve(Fetch(old))
        pointer, new = fixture('new rule')
        root, status = self.resolve(Fetch(new))
        self.assertEqual(root.name, pointer['snapshotId'])
        self.assertFalse(status['knowledge_update']['stale'])

    def test_network_failure_keeps_previous_cache_and_reports_stale(self):
        pointer, responses = fixture('last good rule')
        self.resolve(Fetch(responses))
        def offline(*args):
            raise OSError('private-network-diagnostic-must-not-leak')
        root, status = self.resolve(offline)
        self.assertEqual(root.name, pointer['snapshotId'])
        self.assertTrue(status['knowledge_update']['stale'])
        self.assertNotIn('private-network', json.dumps(status))

    def test_offline_reports_capture_date_without_claiming_a_fresh_check(self):
        def dated(manifest, files):
            manifest['capturedAtUtc'] = '2026-10-19T00:00:00Z'
        _, responses = fixture('dated rule', mutate=dated)
        self.resolve(Fetch(responses))
        def offline(*args):
            raise OSError('offline')
        _, status = self.resolve(offline)
        result = status['knowledge_update']
        self.assertIsNone(result['checkedAtUtc'])
        self.assertEqual(result['snapshotCapturedAtUtc'], '2026-10-19T00:00:00Z')

    def test_no_network_and_no_cache_reports_bundled_fallback(self):
        def offline(*args):
            raise OSError('offline')
        root, status = self.resolve(offline)
        self.assertEqual(root, self.bundle)
        self.assertEqual(status['knowledge_update']['source'], 'bundle')
        self.assertTrue(status['knowledge_update']['stale'])

    def test_corrupt_update_does_not_advance_pointer(self):
        pointer, old = fixture('good rule')
        self.resolve(Fetch(old))
        _, corrupt = fixture('bad rule', extra={'escape.py': b'code'})
        root, status = self.resolve(Fetch(corrupt))
        self.assertEqual(root.name, pointer['snapshotId'])
        self.assertTrue(status['knowledge_update']['stale'])


if __name__ == '__main__':
    unittest.main()
