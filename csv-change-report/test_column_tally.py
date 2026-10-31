"""Synthetic end-to-end checks for the offline column helper."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
PYTHON = [sys.executable] + (['-O'] if sys.flags.optimize else [])


class ColumnTallyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='column tally ')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.report = self.directory / 'report.json'

    def invoke(self, raw):
        self.report.write_bytes(raw)
        result = subprocess.run(PYTHON + [str(ROOT / 'evaluation/column-tally.py'), str(self.report)],
                                cwd=self.directory, capture_output=True)
        self.assertEqual(self.report.read_bytes(), raw)
        return result

    def valid(self):
        return dict(format_version=1, counts=dict(before=3, after=3, added=1, removed=1,
                    changed=1, unchanged=1), changed_cells_by_column={'z': 1, 'a': 1})

    def reject(self, raw):
        result = self.invoke(raw)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertEqual(result.stderr, b'Cannot tally: unreadable, oversized, malformed or inconsistent report.\n')

    def test_real_equal_changed_and_summary_reports(self):
        before = self.directory / 'before.csv'
        after = self.directory / 'after.csv'
        before.write_text('id,z,a\n1,PRIVATE_OLD,x\n2,same,y\n3,gone,z\n')
        for summary in (False, True):
            for changed in (False, True):
                after.write_text('id,z,a\n1,PRIVATE_NEW,new\n2,same,y\n4,added,z\n' if changed else before.read_text())
                command = PYTHON + [str(ROOT / 'csv_change.py'), str(before), str(after), '--key', 'id', '--format', 'json']
                if summary: command.append('--summary-only')
                generated = subprocess.run(command, capture_output=True)
                self.assertEqual(generated.returncode, 0, generated.stderr)
                result = self.invoke(generated.stdout)
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads(result.stdout)
                self.assertEqual(data['changed_records'], int(changed))
                self.assertEqual(data['changed_cells'], 2 * int(changed))
                self.assertEqual(data['columns'], [{'column':'a','changed_cells':int(changed)}, {'column':'z','changed_cells':int(changed)}])
                self.assertNotIn(b'PRIVATE_', result.stdout + result.stderr)

    def test_malformed_json_does_not_echo_content(self):
        self.reject(b'{"PRIVATE_SENTINEL":')

    def test_duplicate_fields(self):
        self.reject(b'{"format_version":1,"format_version":2}')

    def test_unsupported_versions_and_summary_mode(self):
        for version in (True, 0, 3, '1', 2):
            data = self.valid(); data['format_version'] = version
            self.reject(json.dumps(data).encode())

    def test_invalid_counts(self):
        for value in (True, -1, 1.5, '1', None):
            data = self.valid(); data['counts']['changed'] = value
            self.reject(json.dumps(data).encode())

    def test_inconsistent_row_totals(self):
        data = self.valid(); data['counts']['before'] = 99
        self.reject(json.dumps(data).encode())

    def test_invalid_column_counts(self):
        for value in (True, -1, 2, '1', None):
            data = self.valid(); data['changed_cells_by_column']['a'] = value
            self.reject(json.dumps(data).encode())

    def test_missing_or_insufficient_columns(self):
        for columns in (None, [], {}, {'a': 0}, {'': 1}):
            data = self.valid(); data['changed_cells_by_column'] = columns
            self.reject(json.dumps(data).encode())

    def test_bad_top_levels_and_encoding(self):
        for raw in (b'[]', b'null', b'NaN', b'\xff', b'{"x":Infinity}'):
            self.reject(raw)

    def test_size_limit(self):
        self.reject(b' ' * (16 * 1024 * 1024 + 1))

    def test_escaped_column_names(self):
        data = self.valid(); data['changed_cells_by_column'] = {'x\n\u001b': 1}
        result = self.invoke(json.dumps(data).encode())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count(b'\n'), 1)
        self.assertNotIn(b'\x1b', result.stdout)

    def test_missing_file(self):
        result = subprocess.run(PYTHON + [str(ROOT / 'evaluation/column-tally.py'), str(self.report)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')


if __name__ == '__main__':
    unittest.main()
