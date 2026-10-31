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


    def test_stdout_faults_override_check_status(self):
        old = self.put('old.csv', 'id,x\na,1\n')
        new = self.put('new.csv', 'id,x\na,2\n')
        class Fault:
            def __init__(self, mode, fault): self.mode, self.fault = mode, fault
            def write(self, data):
                if self.mode == 'write': raise self.fault('private synthetic exception')
                return len(data)
            def flush(self):
                if self.mode == 'flush': raise self.fault('private synthetic exception')
        for after in [old, new]:
            for fmt in ['json', 'text']:
                for mode in ['write', 'flush']:
                    for fault in [BrokenPipeError, OSError, RuntimeError]:
                        with self.subTest(after=after.name, fmt=fmt, mode=mode, fault=fault):
                            err = io.StringIO()
                            with contextlib.redirect_stdout(Fault(mode, fault)), contextlib.redirect_stderr(err):
                                code = main([str(old), str(after), '--key', 'id', '--format', fmt, '--check'])
                            self.assertEqual(code, 2)
                            self.assertEqual(err.getvalue(), '{"error": "standard output could not be written"}\n')

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux pipe/descriptor regression')
    def test_closed_stdout_pipe_process_status(self):
        import os
        old = self.put('old.csv', 'id,x\na,1\n')
        new = self.put('new.csv', 'id,x\na,2\n')
        tool = str(Path(__file__).with_name('csv_change.py'))
        for after in [old, new]:
            for fmt in ['json', 'text']:
                read_fd, write_fd = os.pipe()
                os.close(read_fd)
                with os.fdopen(write_fd, 'wb') as sink:
                    result = subprocess.run([sys.executable, tool, str(old), str(after), '--key', 'id', '--check', '--format', fmt], stdout=sink, stderr=subprocess.PIPE)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stderr, b'{"error": "standard output could not be written"}\n')

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

    def test_process_check_content_semantics_and_reports(self):
        before = self.root / 'before.csv'
        after = self.root / 'after.csv'
        before.write_text('id,x\na,1\nb,2\n', encoding='utf-8')
        cases = [
            ('id,x\na,1\nb,2\n', 0),
            ('\ufeffx,id\r\n2,b\r\n1,a\r\n', 0),
            ('id,x\na,9\nb,2\n', 1),
            ('id,x\na,1\nb,2\nc,3\n', 1),
            ('id,x\na,1\n', 1),
            ('id,x\na,9\nc,3\n', 1),
        ]
        for index, (data, status) in enumerate(cases):
            after.write_bytes(data.encode('utf-8'))
            snapshots = (before.read_bytes(), after.read_bytes())
            for fmt in ('json', 'text'):
                args = (before, after, '--key', 'id', '--format', fmt)
                baseline = self.run_cli(*args)
                checked = self.run_cli(*args, '--check')
                self.assertEqual((baseline.returncode, checked.returncode), (0, status))
                self.assertEqual((checked.stdout, checked.stderr), (baseline.stdout, ''))
                output = self.root / f'report-{index}-{fmt}'
                saved = self.run_cli(*args, '--check', '--output', output)
                self.assertEqual((saved.returncode, saved.stdout, saved.stderr), (status, '', ''))
                self.assertEqual(output.read_bytes(), baseline.stdout.encode('utf-8'))
                refused = self.run_cli(*args, '--check', '--output', output)
                self.assertEqual((refused.returncode, refused.stdout, refused.stderr),
                                 (2, '', '{"error": "output path already exists"}\n'))
                self.assertEqual(output.read_bytes(), baseline.stdout.encode('utf-8'))
            self.assertEqual((before.read_bytes(), after.read_bytes()), snapshots)

    def test_process_check_empty_and_key_only(self):
        before = self.root / 'before.csv'
        after = self.root / 'after.csv'
        for left, right, status in [('id\n', 'id\n', 0),
                                    ('id\na\n', 'id\na\n', 0),
                                    ('id\na\n', 'id\nb\n', 1)]:
            before.write_text(left)
            after.write_text(right)
            result = self.run_cli(before, after, '--key', 'id', '--check')
            self.assertEqual((result.returncode, result.stderr), (status, ''))
            self.assertEqual(json.loads(result.stdout)['counts']['changed'], 0)

    def test_process_check_errors_take_precedence(self):
        before = self.root / 'before.csv'
        after = self.root / 'after.csv'
        before.write_text('id,x\na,1\n')
        after.write_text('id,x\na,9\n')
        for extra in [('--output', before), ('--output', self.root / 'absent' / 'report'),
                      ('--format', 'PRIVATE_BAD'), ('--che',)]:
            result = self.run_cli(before, after, '--key', 'id', '--check', *extra)
            self.assertEqual((result.returncode, result.stdout), (2, ''))
            self.assertNotIn('PRIVATE_BAD', result.stderr)
        after.write_text('id,x\na,1\na,2\n')
        output = self.root / 'never-created'
        invalid = self.run_cli(before, after, '--key', 'id', '--check', '--output', output)
        self.assertEqual((invalid.returncode, invalid.stdout, invalid.stderr),
                         (2, '', '{"error": "record 2 repeats a key"}\n'))
        self.assertFalse(output.exists())
        after.unlink()
        missing = self.run_cli(before, after, '--key', 'id', '--check')
        self.assertEqual((missing.returncode, missing.stdout, missing.stderr),
                         (2, '', '{"error": "input file could not be read"}\n'))

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
        self.assertEqual(result.stdout, 'csv-change-report 0.1.6-preview\n')
        self.assertEqual(result.stderr, '')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_process_report_version_matches_cli(self):
        version = self.run_cli('--version')
        report = self.run_cli(self.source / 'examples' / 'before.csv',
                              self.source / 'examples' / 'after.csv', '--key', 'id')
        self.assertEqual((version.returncode, report.returncode), (0, 0))
        self.assertEqual((version.stderr, report.stderr), ('', ''))
        self.assertEqual(version.stdout,
                         'csv-change-report ' + json.loads(report.stdout)['tool_version'] + '\n')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_process_text_exact_and_explicit_json(self):
        before = self.source / 'examples' / 'before.csv'
        after = self.source / 'examples' / 'after.csv'
        snapshots = (before.read_bytes(), after.read_bytes())
        default = self.run_cli(before, after, '--key', 'id')
        explicit = self.run_cli(before, after, '--key', 'id', '--format', 'json')
        text = self.run_cli(before, after, '--key', 'id', '--format', 'text')
        for result in (default, explicit, text):
            self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(default.stdout, explicit.stdout)
        self.assertEqual(text.stdout, 'CSV Change Report 0.1.6-preview\n'
                         'Records: before 3, after 3\n'
                         'Changes: added 1, removed 1, changed 1, unchanged 1\n'
                         'Added after records: 2\nRemoved before records: 2\n'
                         'Changed records:\n  before 1 -> after 1: "status"\n'
                         'Changed cells by column:\n  "name": 0\n  "status": 1\n')
        self.assertEqual((before.read_bytes(), after.read_bytes()), snapshots)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_process_text_escapes_headers_and_omits_values(self):
        import csv
        header = 'note\n\x1b[31m\t"雪'
        old, new = self.root / 'old.csv', self.root / 'new.csv'
        for path, value in [(old, 'Private-Old'), (new, 'Private-New')]:
            with path.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerows([['id', header], ['Private-Key', value]])
        snapshots = (old.read_bytes(), new.read_bytes())
        result = self.run_cli(old, new, '--key', 'id', '--format', 'text')
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertIn(json.dumps(header, ensure_ascii=True) + ': 1', result.stdout)
        self.assertNotIn('Private-', result.stdout)
        self.assertNotIn('\x1b', result.stdout)
        self.assertNotIn('\t', result.stdout)
        self.assertNotIn(str(self.root), result.stdout)
        self.assertEqual(len(result.stdout.splitlines()), 9)
        self.assertEqual((old.read_bytes(), new.read_bytes()), snapshots)

    def test_process_text_empty_key_only(self):
        path = self.root / 'empty.csv'
        path.write_text('id\n')
        result = self.run_cli(path, path, '--key', 'id', '--format', 'text')
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(result.stdout, 'CSV Change Report 0.1.6-preview\n'
                         'Records: before 0, after 0\n'
                         'Changes: added 0, removed 0, changed 0, unchanged 0\n'
                         'Added after records: none\nRemoved before records: none\n'
                         'Changed records:\n  none\nChanged cells by column:\n  none\n')

    def test_process_format_errors(self):
        for fmt in ('json', 'text', 'Private-Format'):
            result = self.run_cli('Private-Before', 'Private-After', '--key', 'id', '--format', fmt)
            self.assertEqual((result.returncode, result.stdout), (2, ''))
            message = ('invalid arguments; use --help for usage' if fmt == 'Private-Format'
                       else 'input file could not be read')
            self.assertEqual(json.loads(result.stderr), {'error': message})
            self.assertNotIn('Private-', result.stderr)

    def test_process_output_matches_stdout_and_private_mode(self):
        before = self.source / 'examples' / 'before.csv'
        after = self.source / 'examples' / 'after.csv'
        snapshots = (before.read_bytes(), after.read_bytes())
        for fmt in ('json', 'text'):
            target = self.root / ('report.' + fmt)
            expected = self.run_cli(before, after, '--key', 'id', '--format', fmt)
            result = self.run_cli(before, after, '--key', 'id', '--format', fmt,
                                  '--output', target)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
            self.assertEqual(target.read_bytes(), expected.stdout.encode('utf-8'))
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertEqual((before.read_bytes(), after.read_bytes()), snapshots)

    def test_process_output_refuses_existing_links_and_inputs(self):
        import os
        before = self.root / 'before.csv'
        after = self.root / 'after.csv'
        before.write_text('id,x\na,Private-Old\n')
        after.write_text('id,x\na,Private-New\n')
        snapshots = (before.read_bytes(), after.read_bytes())
        existing = self.root / 'Private-Existing'
        existing.write_bytes(b'Private-Preserved')
        link = self.root / 'Private-Link'
        link.symlink_to(existing)
        dangling = self.root / 'Private-Dangling'
        dangling.symlink_to(self.root / 'absent')
        input_link = self.root / 'Private-Input-Link'
        input_link.symlink_to(before)
        hard = self.root / 'Private-Hardlink'
        os.link(after, hard)
        directory = self.root / 'Private-Directory'
        directory.mkdir()
        for target, message in [
                (before, 'output path matches an input'),
                (after, 'output path matches an input'),
                (before.parent / '.' / before.name, 'output path matches an input'),
                (input_link, 'output path matches an input'),
                *[(p, 'output path already exists') for p in
                  (existing, link, dangling, hard, directory)]]:
            for fmt in ('json', 'text'):
                with self.subTest(target=target.name, fmt=fmt):
                    result = self.run_cli(before, after, '--key', 'id', '--format', fmt,
                                          '--output', target)
                    self.assertEqual((result.returncode, result.stdout), (2, ''))
                    self.assertEqual(json.loads(result.stderr), {'error': message})
                    self.assertNotIn('Private-', result.stderr)
                    self.assertEqual((before.read_bytes(), after.read_bytes()), snapshots)
                    self.assertEqual(existing.read_bytes(), b'Private-Preserved')
                    self.assertTrue(link.is_symlink() and dangling.is_symlink())
                    self.assertFalse((self.root / 'absent').exists())

    def test_process_output_failure_and_invalid_input_create_nothing(self):
        valid = self.root / 'valid.csv'
        valid.write_text('id\na\n')
        target = self.root / 'Private-Missing-Parent' / 'report'
        result = self.run_cli(valid, valid, '--key', 'id', '--output', target)
        self.assertEqual((result.returncode, result.stdout), (2, ''))
        self.assertEqual(json.loads(result.stderr), {'error': 'output file could not be written'})
        self.assertNotIn('Private-', result.stderr)
        self.assertFalse(target.parent.exists())
        target = self.root / 'report'
        result = self.run_cli(self.root / 'missing', valid, '--key', 'id', '--output', target)
        self.assertEqual((result.returncode, result.stdout), (2, ''))
        self.assertEqual(json.loads(result.stderr), {'error': 'input file could not be read'})
        self.assertFalse(target.exists())

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
