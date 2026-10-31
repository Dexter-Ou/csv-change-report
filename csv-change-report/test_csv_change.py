"""Synthetic acceptance tests. Execute only on the isolated build worker."""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from csv_change import InputError, compare, load, main


class ChangeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def put(self, name, text):
        path = self.root / name
        path.write_text(text, encoding='utf-8')
        return path

    def test_core_journey_and_no_cell_values(self):
        old = self.put('old.csv', 'id,name,status\na,Private-A,open\nb,Private-B,open\nc,Private-C,done\n')
        new = self.put('new.csv', 'status,id,name\nclosed,a,Private-A\nopen,d,Private-D\ndone,c,Private-C\n')
        before_bytes, after_bytes = old.read_bytes(), new.read_bytes()
        result = compare(old, new, 'id')
        self.assertEqual(result['counts'], {'before': 3, 'after': 3, 'added': 1, 'removed': 1, 'changed': 1, 'unchanged': 1})
        self.assertEqual(result['changed_records'], [{'before_record': 1, 'after_record': 1, 'columns': ['status']}])
        self.assertEqual(result['added_after_records'], [2])
        self.assertEqual(result['removed_before_records'], [2])
        self.assertNotIn('Private-', json.dumps(result))
        self.assertEqual((old.read_bytes(), new.read_bytes()), (before_bytes, after_bytes))

    def test_quoted_multiline_bom_and_exact_values(self):
        old = self.put('old.csv', '\ufeffid,note\na,"line1\nline2"\n')
        new = self.put('new.csv', 'id,note\na,"line1\nline2 "\n')
        self.assertEqual(compare(old, new, 'id')['counts']['changed'], 1)

    def test_reordered_records_unchanged(self):
        old = self.put('old.csv', 'id,x\na,1\nb,2\n')
        new = self.put('new.csv', 'id,x\nb,2\na,1\n')
        self.assertEqual(compare(old, new, 'id')['counts']['unchanged'], 2)

    def test_reject_ambiguous_inputs(self):
        cases = ['', 'id,id\na,b\n', 'id,x\na,1\na,2\n', 'id,x\n,1\n',
                 'id,x\na\n', 'id,x\na,"unterminated\n', 'id,\na,1\n', 'id,x\na,\x00\n']
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(InputError):
                    load(self.put('bad.csv', text), 'id')

    def test_schema_change_rejected(self):
        with self.assertRaises(InputError):
            compare(self.put('a.csv', 'id,x\na,1\n'), self.put('b.csv', 'id,y\na,1\n'), 'id')

    def test_missing_key_and_invalid_encoding(self):
        with self.assertRaises(InputError):
            load(self.put('a.csv', 'other\na\n'), 'id')
        path = self.root / 'invalid.csv'
        path.write_bytes(b'id\n\xff\n')
        with self.assertRaises(InputError):
            load(path, 'id')

    def test_limits(self):
        path = self.put('a.csv', 'id\na\nb\n')
        with patch('csv_change.MAX_ROWS', 1), self.assertRaises(InputError):
            load(path, 'id')
        with patch('csv_change.MAX_BYTES', 2), self.assertRaises(InputError):
            load(path, 'id')

    def test_column_and_cell_limits(self):
        path = self.put('wide.csv', 'id,x,y\na,1,2\n')
        with patch('csv_change.MAX_COLUMNS', 2), self.assertRaises(InputError):
            load(path, 'id')
        # Header-only inputs must also respect the column limit.
        empty = self.put('header.csv', 'id,x,y\n')
        with patch('csv_change.MAX_COLUMNS', 2), self.assertRaises(InputError):
            load(empty, 'id')
        path = self.put('cells.csv', 'id,x\na,1\nb,2\n')
        with patch('csv_change.MAX_CELLS', 4):
            self.assertEqual(len(load(path, 'id')[1]), 2)
        with patch('csv_change.MAX_CELLS', 3), self.assertRaises(InputError):
            load(path, 'id')

    def test_deterministic_order_and_cli_bytes(self):
        old = self.put('old.csv', 'id,z,a\nb,0,0\na,0,0\nr,0,0\n')
        new = self.put('new.csv', 'a,id,z\n1,a,1\n1,b,1\n0,y,0\n0,x,0\n')
        result = compare(old, new, 'id')
        self.assertEqual(result['added_after_records'], [3, 4])
        self.assertEqual(result['removed_before_records'], [3])
        self.assertEqual(result['changed_records'], [
            {'before_record': 1, 'after_record': 2, 'columns': ['z', 'a']},
            {'before_record': 2, 'after_record': 1, 'columns': ['z', 'a']}])
        outputs = []
        for _ in range(3):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(main([str(old), str(new), '--key', 'id']), 0)
            outputs.append(stdout.getvalue())
        self.assertEqual(outputs, [outputs[0]] * 3)
        self.assertEqual(json.loads(outputs[0]), result)

    def test_cli_argument_errors_do_not_echo_private_text(self):
        for args in [[], ['Private-Path'],
                     ['Private-Before', 'Private-After', '--key', 'id', '--Private-Option'],
                     ['Private-Before', 'Private-After', '--key'],
                     ['Private-Before', 'Private-After', '--ke', 'Private-Key']]:
            with self.subTest(args=args):
                stderr, stdout = io.StringIO(), io.StringIO()
                with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
                    self.assertEqual(main(args), 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertEqual(json.loads(stderr.getvalue()),
                                 {'error': 'invalid arguments; use --help for usage'})
                self.assertNotIn('Private-', stderr.getvalue())

    def test_documented_fixture_matches_expected_report(self):
        root = Path(__file__).resolve().parent / 'examples'
        expected = json.loads((root / 'expected-report.json').read_text(encoding='utf-8'))
        self.assertEqual(compare(root / 'before.csv', root / 'after.csv', 'id'), expected)

    def test_empty_exports_and_cli_error(self):
        path = self.put('empty.csv', 'id,x\n')
        self.assertEqual(compare(path, path, 'id')['counts']['before'], 0)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main([str(self.root / 'missing'), str(path), '--key', 'id'])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stderr.getvalue()), {'error': 'input file could not be read'})


class ProcessTests(unittest.TestCase):
    """Exercise the real entry point; run only on the isolated worker."""
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = Path(__file__).resolve().parent

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(self.source / 'csv_change.py'), *map(str, args)],
            cwd=self.root, capture_output=True, text=True, encoding='utf-8',
            timeout=15, check=False)

    def test_process_fixture_from_unrelated_directory(self):
        before = self.source / 'examples' / 'before.csv'
        after = self.source / 'examples' / 'after.csv'
        snapshots = (before.read_bytes(), after.read_bytes())
        expected = json.loads((self.source / 'examples' / 'expected-report.json').read_text())
        first = self.run_cli(before, after, '--key', 'id')
        second = self.run_cli(before, after, '--key', 'id')
        for result in (first, second):
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, '')
            self.assertEqual(json.loads(result.stdout), expected)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual((before.read_bytes(), after.read_bytes()), snapshots)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_process_version(self):
        result = self.run_cli('--version')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'csv-change-report 0.1.1-preview\n')
        self.assertEqual(result.stderr, '')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_process_help(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, '')
        self.assertIn('--key', result.stdout)
        self.assertIn('usage:', result.stdout)

    def test_process_argument_errors(self):
        for args in [(), ('Private-Path',),
                     ('Private-Before', 'Private-After', '--ke', 'Private-Key')]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertEqual(json.loads(result.stderr),
                                 {'error': 'invalid arguments; use --help for usage'})
                self.assertNotIn('Private-', result.stderr)

    def test_process_input_errors(self):
        valid = self.root / 'valid.csv'
        valid.write_text('id,value\na,Private-Value\n', encoding='utf-8')
        invalid = self.root / 'Private-Invalid.csv'
        invalid.write_bytes(b'id,value\na,\xff\n')
        duplicate = self.root / 'Private-Duplicate.csv'
        duplicate.write_text('id,value\na,Private-One\na,Private-Two\n', encoding='utf-8')
        for before, message in [
                (self.root / 'Private-Missing.csv', 'input file could not be read'),
                (invalid, 'input must be UTF-8'),
                (duplicate, 'record 2 repeats a key')]:
            with self.subTest(before=before.name):
                result = self.run_cli(before, valid, '--key', 'id')
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertEqual(json.loads(result.stderr), {'error': message})
                self.assertNotIn('Private-', result.stderr)


if __name__ == '__main__':
    unittest.main()
