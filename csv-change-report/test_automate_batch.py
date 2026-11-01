"""Offline synthetic CLI regressions for the checked automation example."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / 'evaluation' / 'automate-batch.py'


class AutomationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / 'data space'
        self.data.mkdir()
        self.before = self.data / 'before.csv'
        self.after = self.data / 'after.csv'
        self.before.write_bytes(b'id,value\n1,a\n')
        self.after.write_bytes(b'id,value\n1,b\n')
        self.manifest = self.data / 'batch.json'
        self.reports = self.root / 'report space'

    def write_manifest(self, kinds):
        pairs = []
        for kind in kinds:
            pairs.append({'before': self.before.name,
                          'after': {'equal': self.before.name,
                                    'changed': self.after.name,
                                    'error': 'missing.csv'}[kind], 'key': 'id'})
        self.manifest.write_text(json.dumps({'version': 1, 'pairs': pairs}),
                                 encoding='utf-8')

    def run_wrapper(self, code, status, count, reports=None, arguments=None):
        # Check the whole machine-readable contract and preserve input bytes.
        originals = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in self.data.iterdir() if p.is_file()}
        result = subprocess.run([sys.executable,
            *(['-' + 'O' * sys.flags.optimize] if sys.flags.optimize else []),
            str(SCRIPT),
            *(arguments if arguments is not None else
              [str(self.manifest), str(reports or self.reports)])],
            cwd=self.root, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, status, result.stderr)
        self.assertEqual(result.stderr, b'')
        self.assertEqual(json.loads(result.stdout),
                         {'version': 1, 'code': code, 'status': status,
                          'pair_count': count})
        for path, digest in originals.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        return result

    def check_table(self, statuses):
        lines = (self.reports / 'status.tsv').read_text(encoding='utf-8').splitlines()
        self.assertEqual(lines[0], 'pair\tstatus\treport\tdiagnostic')
        self.assertEqual(len(lines), len(statuses) + 1)
        for index, (line, status) in enumerate(zip(lines[1:], statuses), 1):
            stem = f'pair-{index:04d}'
            report = stem + '.json' if status in (0, 1) else '-'
            self.assertEqual(line.split('\t'),
                             [stem, str(status), report, stem + '.stderr'])
            diagnostic = self.reports / (stem + '.stderr')
            self.assertTrue(diagnostic.is_file())
            if status in (0, 1):
                self.assertEqual(diagnostic.read_bytes(), b'')
                payload = json.loads((self.reports / report).read_bytes())
                self.assertEqual(payload['counts']['changed'], status)
            else:
                self.assertFalse((self.reports / (stem + '.json')).exists())
                self.assertTrue(diagnostic.read_bytes())

    def test_unicode_and_space_filenames_from_other_directory(self):
        self.before = self.data / 'before café 数据.csv'
        self.after = self.data / 'after café 数据.csv'
        self.before.write_bytes(b'id,value\n1,a\n')
        self.after.write_bytes(b'id,value\n1,b\n')
        self.manifest = self.data / 'manifest café 数据.json'
        scenarios = [(['equal'], 'EQUAL', 0, [0]),
                     (['equal', 'changed'], 'CHANGED', 1, [0, 1]),
                     (['error', 'equal', 'changed'], 'E_COMPARISON', 2, [2, 0, 1])]
        for index, (kinds, code, status, statuses) in enumerate(scenarios):
            with self.subTest(code=code):
                self.reports = self.root / f'reports café 数据 {index}'
                self.write_manifest(kinds)
                self.run_wrapper(code, status, len(kinds))
                self.check_table(statuses)
                snapshot = {p.name: p.read_bytes() for p in self.reports.iterdir()}
                self.run_wrapper('E_OUTPUT', 2, len(kinds))
                self.assertEqual({p.name: p.read_bytes() for p in self.reports.iterdir()},
                                 snapshot)

    def test_quoted_multiline_and_crlf_records(self):
        # Physical lines inside quoted fields must not become extra records.
        for index, ending in enumerate((b'\n', b'\r\n')):
            with self.subTest(record_ending=repr(ending)):
                before = ending.join((b'id,value', b'1,"alpha,beta"',
                                      b'2,"first\nsecond"',
                                      b'3,"say ""hello"""')) + ending
                after = before.replace(b'first\nsecond', b'first\nrevised')
                self.before.write_bytes(before)
                self.after.write_bytes(after)
                for offset, (kinds, code, status, statuses) in enumerate((
                        (['equal'], 'EQUAL', 0, [0]),
                        (['equal', 'changed'], 'CHANGED', 1, [0, 1]),
                        (['error', 'equal', 'changed'], 'E_COMPARISON', 2, [2, 0, 1]))):
                    self.reports = self.root / f'quoted reports {index}-{offset}'
                    self.write_manifest(kinds)
                    self.run_wrapper(code, status, len(kinds))
                    self.check_table(statuses)
                    for pair, pair_status in enumerate(statuses, 1):
                        if pair_status in (0, 1):
                            payload = json.loads((self.reports /
                                f'pair-{pair:04d}.json').read_bytes())
                            self.assertEqual(payload['counts']['unchanged'],
                                             3 - pair_status)
                            self.assertEqual(payload['counts']['added'], 0)
                            self.assertEqual(payload['counts']['removed'], 0)
                    snapshot = {x.name: x.read_bytes() for x in self.reports.iterdir()}
                    self.run_wrapper('E_OUTPUT', 2, len(kinds))
                    self.assertEqual({x.name: x.read_bytes() for x in self.reports.iterdir()},
                                     snapshot)

    def test_all_equal(self):
        self.write_manifest(['equal', 'equal'])
        self.run_wrapper('EQUAL', 0, 2)
        self.check_table([0, 0])

    def test_equal_and_changed(self):
        self.write_manifest(['equal', 'changed'])
        self.run_wrapper('CHANGED', 1, 2)
        self.check_table([0, 1])

    def test_error_dominates_and_later_pairs_complete(self):
        self.write_manifest(['error', 'equal', 'changed'])
        self.run_wrapper('E_COMPARISON', 2, 3)
        self.check_table([2, 0, 1])

    def test_error_last_preserves_successful_reports(self):
        self.write_manifest(['equal', 'changed', 'error'])
        self.run_wrapper('E_COMPARISON', 2, 3)
        self.check_table([0, 1, 2])

    def test_missing_output_parent(self):
        self.write_manifest(['equal'])
        parent = self.root / 'missing parent'
        self.run_wrapper('E_STATUS', 2, 1, reports=parent / 'reports')
        self.assertFalse(parent.exists())

    def test_output_parent_is_file(self):
        self.write_manifest(['equal'])
        parent = self.root / 'file parent'
        parent.write_bytes(b'preserve this parent')
        self.run_wrapper('E_STATUS', 2, 1, reports=parent / 'reports')
        self.assertEqual(parent.read_bytes(), b'preserve this parent')

    def require_denied_creation(self, directory):
        # Observe a real denial; chmod bits alone do not establish enforcement.
        if os.name != 'posix':
            self.skipTest('POSIX directory permissions required')
        original_mode = directory.stat().st_mode & 0o7777
        self.addCleanup(directory.chmod, original_mode)
        directory.chmod(0o555)
        probe = directory / 'permission probe'
        try:
            probe.mkdir()
        except PermissionError:
            return
        else:
            probe.rmdir()
            self.skipTest('runtime can bypass directory write permissions')

    def test_denied_output_parent_and_fresh_output(self):
        self.write_manifest(['changed'])
        parent = self.root / 'denied parent'
        parent.mkdir()
        sentinel = parent / 'sentinel'
        sentinel.write_bytes(b'preserve parent contents')
        self.require_denied_creation(parent)
        self.run_wrapper('E_STATUS', 2, 1, reports=parent / 'reports')
        self.assertEqual({p.name: p.read_bytes() for p in parent.iterdir()},
                         {'sentinel': b'preserve parent contents'})
        self.run_wrapper('CHANGED', 1, 1)
        self.check_table([1])

    def test_read_only_existing_reports_are_preserved(self):
        self.write_manifest(['changed'])
        self.run_wrapper('CHANGED', 1, 1)
        self.check_table([1])
        originals = {p.name: p.read_bytes() for p in self.reports.iterdir()}
        self.require_denied_creation(self.reports)
        for path in self.reports.iterdir():
            original_mode = path.stat().st_mode & 0o7777
            self.addCleanup(path.chmod, original_mode)
            path.chmod(0o444)
        self.run_wrapper('E_OUTPUT', 2, 1)
        self.assertEqual({p.name: p.read_bytes() for p in self.reports.iterdir()},
                         originals)
        self.run_wrapper('CHANGED', 1, 1, reports=self.root / 'fresh reports')

    def test_existing_reports_are_never_reused(self):
        self.write_manifest(['error', 'changed'])
        self.run_wrapper('E_COMPARISON', 2, 2)
        originals = {p.name: p.read_bytes() for p in self.reports.iterdir()}
        self.run_wrapper('E_OUTPUT', 2, 2)
        self.assertEqual({p.name: p.read_bytes() for p in self.reports.iterdir()}, originals)

    def test_existing_file_is_preserved(self):
        self.write_manifest(['equal'])
        self.reports.write_bytes(b'original output file')
        self.run_wrapper('E_OUTPUT', 2, 1)
        self.assertEqual(self.reports.read_bytes(), b'original output file')

    def test_malformed_manifest_creates_no_reports(self):
        self.manifest.write_bytes(b'{')
        self.run_wrapper('E_PREFLIGHT', 2, None)
        self.assertFalse(self.reports.exists())

    def test_argument_error_creates_no_reports(self):
        self.run_wrapper('E_ARGUMENTS', 2, None, arguments=[])
        self.assertFalse(self.reports.exists())


if __name__ == '__main__':
    unittest.main()
