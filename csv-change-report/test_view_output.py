"""Synthetic HTML output failure and fresh-path recovery regressions."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import view_report

ROOT = Path(__file__).resolve().parent

class ViewerOutputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.source = ROOT / 'examples/expected-report.json'
        self.original = self.source.read_bytes()
        self.expected = view_report.render(json.loads(self.original)).encode()

    def tearDown(self):
        self.assertEqual(self.source.read_bytes(), self.original)

    def invoke(self, out):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), patch.object(sys, 'argv', ['view_report.py', str(self.source), '--output', str(out)]):
            status = view_report.main()
        return status, stdout.getvalue(), stderr.getvalue()

    def test_success_and_existing_destinations(self):
        out = self.work / 'complete.html'
        self.assertEqual(self.invoke(out)[0], 0)
        self.assertEqual(out.read_bytes(), self.expected)
        if sys.platform.startswith('linux'):
            self.assertEqual(out.stat().st_mode & 0o777, 0o600)
        directory = self.work / 'directory'; directory.mkdir()
        paths = [out, directory]
        if hasattr(os, 'symlink'):
            for name, target in [('link', out), ('dangling', self.work / 'absent')]:
                p = self.work / name; p.symlink_to(target); paths.append(p)
        for target in paths:
            with self.subTest(target=target.name):
                before = os.lstat(target)
                status, stdout, stderr = self.invoke(target)
                self.assertEqual(status, 2); self.assertFalse(stdout)
                self.assertIn('E_OUTPUT:', stderr)
                self.assertEqual(os.lstat(target), before)
                self.assertFalse(list(self.work.glob('.csv-view-*')))
        self.assertEqual(out.read_bytes(), self.expected)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux RLIMIT_FSIZE required')
    def test_real_file_size_failure_and_recovery(self):
        import resource
        for limit in (0, 128):
            with self.subTest(limit=limit):
                out = self.work / ('limit-%s.html' % limit)
                def setup():
                    signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
                    resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
                r = subprocess.run([sys.executable, str(ROOT / 'view_report.py'),
                                    str(self.source), '--output', str(out)],
                                   capture_output=True, preexec_fn=setup, timeout=15)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertFalse(r.stdout); self.assertIn(b'E_OUTPUT:', r.stderr)
                self.assertFalse(out.exists())
                self.assertFalse(list(self.work.glob('.csv-view-*')))
                self.assertEqual(self.invoke(out)[0], 0)
                self.assertEqual(out.read_bytes(), self.expected)

    def test_unsupported_link_and_late_collision(self):
        for collision in (False, True):
            out = self.work / ('collision' if collision else 'unsupported')
            def link(src, dst):
                if collision:
                    with open(dst, 'xb') as f: f.write(b'winner')
                    raise FileExistsError()
                raise OSError('synthetic unsupported link')
            with patch.object(view_report.os, 'link', side_effect=link):
                status, stdout, stderr = self.invoke(out)
            self.assertEqual(status, 2); self.assertFalse(stdout)
            self.assertIn('E_OUTPUT:', stderr)
            self.assertFalse(list(self.work.glob('.csv-view-*')))
            if collision: self.assertEqual(out.read_bytes(), b'winner')
            else: self.assertFalse(out.exists())

    def test_cleanup_failure_state_and_same_path_refusal(self):
        real_unlink = os.unlink
        for committed in (True, False):
            directory = self.work / str(committed); directory.mkdir()
            out = directory / 'report.html'
            def unlink(path, *args, **kwargs):
                if '.csv-view-' in str(path): raise PermissionError('synthetic cleanup denial')
                return real_unlink(path, *args, **kwargs)
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(view_report.os, 'unlink', side_effect=unlink))
                if not committed:
                    stack.enter_context(patch.object(view_report.os, 'link', side_effect=OSError('synthetic link error')))
                status, stdout, stderr = self.invoke(out)
            self.assertEqual(status, 2); self.assertFalse(stdout)
            lines = stderr.splitlines()
            diagnostic = json.loads(lines[0].split('E_OUTPUT: ', 1)[1])
            self.assertEqual(diagnostic['output_committed'], committed)
            self.assertIs(diagnostic['cleanup_required'], True)
            self.assertEqual(len(lines), 1 if committed else 2)
            self.assertNotIn(str(self.work), stderr)
            siblings = list(directory.glob('.csv-view-*'))
            self.assertEqual(len(siblings), 1)
            self.assertEqual(siblings[0].read_bytes(), self.expected)
            self.assertEqual(out.exists(), committed)
            if committed:
                self.assertEqual(out.stat().st_ino, siblings[0].stat().st_ino)
                self.assertEqual(self.invoke(out)[0], 2)
                self.assertEqual(out.read_bytes(), self.expected)
                self.assertTrue(siblings[0].exists())
            siblings[0].unlink()
            fresh = directory / 'recovered.html'
            self.assertEqual(self.invoke(fresh)[0], 0)
            self.assertEqual(fresh.read_bytes(), self.expected)

if __name__ == '__main__':
    unittest.main()
