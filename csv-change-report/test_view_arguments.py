"""Synthetic regression tests for argument text in viewer diagnostics."""
import contextlib
import io
import sys
import unittest
from unittest.mock import patch
import view_report


class ViewerArgumentTests(unittest.TestCase):
    def test_errors_omit_argument_and_invocation_text(self):
        marker = 'SYNTHETIC_PRIVATE_PATH_52a07a'
        cases = [
            ['report.json', '--output', 'out.html', marker],
            ['report.json', '--output', 'out.html', '--' + marker],
            [marker, '--output'],
            [marker],
            ['report.json', '--output', 'out.html', '--before-csv', marker],
        ]
        for args in cases:
            with self.subTest(args=args):
                out, err = io.StringIO(), io.StringIO()
                with patch.object(sys, 'argv', [marker + '/view_report.py', *args]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as raised:
                        view_report.main()
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(out.getvalue(), '')
                self.assertEqual(err.getvalue(), 'E_ARGUMENT: invalid arguments; use --help for usage.\n')
                self.assertNotIn(marker, err.getvalue())

    def test_help_uses_stable_program_name(self):
        out = io.StringIO()
        with patch.object(sys, 'argv', ['SYNTHETIC_PRIVATE_PATH/view_report.py', '--help']), contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as raised:
                view_report.main()
        self.assertEqual(raised.exception.code, 0)
        self.assertIn('csv-change-view', out.getvalue())
        self.assertNotIn('SYNTHETIC_PRIVATE_PATH', out.getvalue())


if __name__ == '__main__':
    unittest.main()
