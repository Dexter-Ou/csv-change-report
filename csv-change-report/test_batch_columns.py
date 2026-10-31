"""Synthetic CLI checks for optional batch column counts."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from csv_change import compare

ROOT = Path(__file__).resolve().parent
PYTHON = [sys.executable] + (['-O'] if sys.flags.optimize else [])

class BatchColumnTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='batch columns ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.table = self.root / 'status.tsv'
        self.before = self.root / 'before.csv'
        self.after = self.root / 'after.csv'
        self.before.write_text('id,z,a\n1,PRIVATE_OLD,x\n')
        self.after.write_text('id,z,a\n1,PRIVATE_NEW,y\n')

    def report(self, index, equal=False, summary=True):
        data = compare(self.before, self.before if equal else self.after, 'id', summary_only=summary)
        path = self.root / f'pair-{index:04d}.json'
        path.write_text(json.dumps(data))
        return path

    def invoke(self, statuses, expected=None, extra=()):
        lines = ['pair\tstatus\treport\tdiagnostic']
        for i, status in enumerate(statuses, 1):
            stem = f'pair-{i:04d}'
            lines.append(f'{stem}\t{status}\t' + (stem+'.json' if status in (0,1) else '-') + f'\t{stem}.stderr')
        self.table.write_text('\n'.join(lines)+'\n')
        before = {p.name:p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        r = subprocess.run(PYTHON + [str(ROOT/'evaluation/batch-totals.py'),str(self.table),
            '--expected-pairs',str(expected or len(statuses)), '--column-counts'] + list(extra),capture_output=True)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir() if p.is_file()})
        self.assertNotIn(b'PRIVATE_',r.stdout+r.stderr)
        return r

    def test_equal_and_changed_both_report_formats(self):
        for summary in (True,False):
            self.report(1,equal=True,summary=summary);self.report(2,summary=summary)
            r=self.invoke([0,1]);self.assertEqual(r.returncode,1,r.stderr)
            d=json.loads(r.stdout);self.assertFalse(d['partial'])
            self.assertEqual(d['column_tally'],dict(reports=2,changed_records=1,changed_cells=2,
                columns=[dict(column='a',changed_cells=1),dict(column='z',changed_cells=1)]))

    def test_sums_repeated_columns(self):
        self.report(1);self.report(2)
        r=self.invoke([1,1]);d=json.loads(r.stdout)
        self.assertEqual(r.returncode,1);self.assertEqual(d['column_tally']['changed_cells'],4)
        self.assertEqual(d['column_tally']['columns'][0]['changed_cells'],2)

    def test_mixed_error_is_partial(self):
        self.report(1);(self.root/'pair-0002.json').write_text('PRIVATE_STALE')
        r=self.invoke([1,2]);d=json.loads(r.stdout)
        self.assertEqual(r.returncode,2);self.assertTrue(d['partial'])
        self.assertEqual(d['error'],1);self.assertEqual(d['column_tally']['reports'],1)

    def test_incomplete_is_partial(self):
        self.report(1,equal=True)
        r=self.invoke([0],expected=3);d=json.loads(r.stdout)
        self.assertEqual(r.returncode,2);self.assertEqual(d['incomplete'],2)
        self.assertTrue(d['partial']);self.assertEqual(d['column_tally']['changed_cells'],0)

    def test_all_errors_has_explicit_empty_tally(self):
        r=self.invoke([2,9]);d=json.loads(r.stdout)
        self.assertEqual(r.returncode,2);self.assertEqual(d['column_tally']['reports'],0)
        self.assertEqual(d['column_tally']['columns'],[]);self.assertTrue(d['partial'])

    def test_unstarted_table(self):
        r=self.invoke([],expected=2);d=json.loads(r.stdout)
        self.assertEqual(r.returncode,2);self.assertEqual(d['completed'],0);self.assertTrue(d['partial'])

    def test_missing_or_malformed_success_report_no_totals(self):
        for raw in (None,'{"PRIVATE_SENTINEL":','{"format_version":1,"format_version":1}'):
            p=self.root/'pair-0001.json'
            if raw is None:
                p.unlink(missing_ok=True)
            else:p.write_text(raw)
            r=self.invoke([1]);self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,b'')
            self.assertTrue(r.stderr.startswith(b'Cannot summarize:'))

    def test_equal_status_contradiction(self):
        self.report(1);r=self.invoke([0]);self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,b'')

    def test_combined_row_counts(self):
        self.report(1);r=self.invoke([1],extra=['--row-counts']);d=json.loads(r.stdout)
        self.assertEqual(r.returncode,1);self.assertEqual(d['rows']['changed'],1)
        self.assertEqual(d['column_tally']['changed_records'],1)

    def test_added_only_is_valid_changed_status(self):
        self.before.write_text('id,z,a\n')
        self.report(1);r=self.invoke([1]);d=json.loads(r.stdout)
        self.assertEqual(r.returncode,1);self.assertFalse(d['partial'])
        self.assertEqual(d['column_tally']['changed_cells'],0)

if __name__ == '__main__':unittest.main()
