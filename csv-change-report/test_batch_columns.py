"""Synthetic CLI checks for optional batch column counts."""
import json
import contextlib
import io
import runpy
from unittest.mock import patch
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

    def invoke(self, statuses, expected=None, extra=(), table_text=None, aggregate=True):
        lines = ['pair\tstatus\treport\tdiagnostic']
        for i, status in enumerate(statuses, 1):
            stem = f'pair-{i:04d}'
            lines.append(f'{stem}\t{status}\t' + (stem+'.json' if status in (0,1) else '-') + f'\t{stem}.stderr')
        self.table.write_text(table_text if table_text is not None else '\n'.join(lines)+'\n')
        before = {p.name:p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        r = subprocess.run(PYTHON + [str(ROOT/'evaluation/batch-totals.py'),str(self.table),
            '--expected-pairs',str(expected or len(statuses))] + (['--column-counts'] if aggregate else []) + list(extra),capture_output=True)
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

    def test_combined_options_open_each_report_once(self):
        module = runpy.run_path(str(ROOT/'evaluation/batch-totals.py'))
        for summary in (True, False):
            for options in (['--column-counts'], ['--pair-column-counts'],
                            ['--column-counts', '--pair-column-counts']):
                with self.subTest(summary=summary, options=options):
                    self.report(1, equal=True, summary=summary)
                    self.report(2, summary=summary)
                    self.invoke([0, 1])
                    before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
                    opens = {}
                    original = Path.open
                    def open_once(path, *args, **kwargs):
                        if path.parent == self.root and path.suffix == '.json':
                            opens[path.name] = opens.get(path.name, 0) + 1
                            if opens[path.name] > 1:
                                raise OSError('synthetic second-read refusal')
                        return original(path, *args, **kwargs)
                    stdout, stderr = io.StringIO(), io.StringIO()
                    argv = ['batch-totals', str(self.table), '--expected-pairs', '2',
                            '--row-counts'] + options
                    with patch.object(sys, 'argv', argv), patch.object(Path, 'open', open_once), \
                            contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        code = module['main']()
                    self.assertEqual(code, 1, stderr.getvalue())
                    self.assertEqual(opens, {'pair-0001.json': 1, 'pair-0002.json': 1})
                    data = json.loads(stdout.getvalue())
                    self.assertEqual(data['rows'], dict(added=0, removed=0, changed=1, unchanged=1))
                    if '--column-counts' in options:
                        self.assertEqual(data['column_tally']['changed_records'], 1)
                    if '--pair-column-counts' in options:
                        self.assertEqual([x['changed_records'] for x in data['pair_column_tallies']], [0, 1])
                    self.assertNotIn('PRIVATE_', stdout.getvalue() + stderr.getvalue())
                    self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()})

    def test_added_only_is_valid_changed_status(self):
        self.before.write_text('id,z,a\n')
        self.report(1);r=self.invoke([1]);d=json.loads(r.stdout)
        self.assertEqual(r.returncode,1);self.assertFalse(d['partial'])
        self.assertEqual(d['column_tally']['changed_cells'],0)

    def test_rejects_report_path_and_name_substitutions(self):
        self.report(1)
        for name in ('../pair-0001.json', '/pair-0001.json',
                     r'..\pair-0001.json', 'sub/pair-0001.json',
                     './pair-0001.json', 'pair-0002.json', '-',
                     'pair-0001.json ', 'PAIR-0001.json'):
            for extra in ((), ('--row-counts',)):
                with self.subTest(name=name, extra=extra):
                    table = 'pair\tstatus\treport\tdiagnostic\n' + (
                        f'pair-0001\t1\t{name}\tpair-0001.stderr\n')
                    r = self.invoke([1], extra=extra, table_text=table)
                    self.assertEqual(r.returncode, 2)
                    self.assertEqual(r.stdout, b'')
                    self.assertTrue(r.stderr.startswith(b'Cannot summarize:'))

    def test_rejects_pair_and_diagnostic_substitutions(self):
        self.report(1)
        for pair, diagnostic in (
                ('../pair-0001', 'pair-0001.stderr'),
                ('pair-0002', 'pair-0001.stderr'),
                ('pair-0001', '../pair-0001.stderr'),
                ('pair-0001', '/pair-0001.stderr'),
                ('pair-0001', 'pair-0002.stderr'),
                ('pair-0001', '-')):
            with self.subTest(pair=pair, diagnostic=diagnostic):
                table = 'pair\tstatus\treport\tdiagnostic\n' + (
                    f'{pair}\t1\tpair-0001.json\t{diagnostic}\n')
                r = self.invoke([1], table_text=table)
                self.assertEqual(r.returncode, 2)
                self.assertEqual(r.stdout, b'')

    def test_rejects_report_name_on_failed_pair(self):
        self.report(1)
        table = ('pair\tstatus\treport\tdiagnostic\n'
                 'pair-0001\t2\tpair-0001.json\tpair-0001.stderr\n')
        r = self.invoke([2], table_text=table)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, b'')

    def test_rejects_malformed_table_records(self):
        self.report(1)
        header = 'pair\tstatus\treport\tdiagnostic\n'
        row = 'pair-0001\t1\tpair-0001.json\tpair-0001.stderr'
        for text in (header + row, header + row + '\textra\n',
                     header + row + '\n' + row + '\n',
                     header + row.replace('\t1\t', '\t01\t') + '\n',
                     header + row.replace('\t1\t', '\t-1\t') + '\n'):
            with self.subTest(text=text):
                r = self.invoke([1], table_text=text)
                self.assertEqual(r.returncode, 2)
                self.assertEqual(r.stdout, b'')

    def test_same_names_merge_across_different_schemas(self):
        self.report(1)
        self.before.write_text('id,a,other\n1,old,same\n')
        self.after.write_text('id,a,other\n1,new,same\n')
        self.report(2)
        r = self.invoke([1, 1])
        self.assertEqual(r.returncode, 1, r.stderr)
        tally = json.loads(r.stdout)['column_tally']
        self.assertEqual(tally['columns'], [dict(column='a', changed_cells=2),
                                          dict(column='other', changed_cells=0),
                                          dict(column='z', changed_cells=1)])
        self.assertEqual(tally['changed_cells'], 3)
        self.assertEqual(tally['reports'], 2)

    def test_column_names_are_data_and_json_escaped(self):
        import csv
        names = ['../report', 'a\tb', 'line\nbreak', 'é', 'A', 'a']
        for path, value in ((self.before, 'old'), (self.after, 'new')):
            with path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id'] + names)
                writer.writerow(['1'] + [value] * len(names))
        self.report(1)
        r = self.invoke([1])
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertEqual([c['column'] for c in json.loads(r.stdout)['column_tally']['columns']],
                         sorted(names))
        self.assertEqual(r.stdout.count(b'\n'), 1)
        self.assertNotIn(b'\t', r.stdout)

    def test_per_pair_separates_unrelated_schemas_both_formats(self):
        for summary in (True, False):
            self.before.write_text('id,z,a\n1,PRIVATE_OLD,x\n')
            self.after.write_text('id,z,a\n1,PRIVATE_NEW,y\n')
            self.report(1, summary=summary)
            self.before.write_text('id,a,other\n1,old,same\n')
            self.after.write_text('id,a,other\n1,new,same\n')
            self.report(2, summary=summary)
            r = self.invoke([1, 1], extra=['--pair-column-counts'], aggregate=False)
            self.assertEqual(r.returncode, 1, r.stderr)
            d = json.loads(r.stdout)
            self.assertNotIn('column_tally', d)
            self.assertFalse(d['partial'])
            pairs = d['pair_column_tallies']
            self.assertEqual([p['pair'] for p in pairs], ['pair-0001', 'pair-0002'])
            self.assertEqual([p['changed_cells'] for p in pairs], [2, 1])
            self.assertEqual(pairs[0]['columns'], [dict(column='a', changed_cells=1), dict(column='z', changed_cells=1)])
            self.assertEqual(pairs[1]['columns'], [dict(column='a', changed_cells=1), dict(column='other', changed_cells=0)])

    def test_per_pair_combined_options(self):
        self.report(1, equal=True); self.report(2)
        r = self.invoke([0, 1], extra=['--pair-column-counts', '--row-counts'])
        self.assertEqual(r.returncode, 1, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual(d['rows']['changed'], 1)
        self.assertEqual(d['column_tally']['changed_cells'], 2)
        self.assertEqual([p['changed_records'] for p in d['pair_column_tallies']], [0, 1])

    def test_per_pair_partial_omits_failed_stale_report(self):
        self.report(1)
        (self.root/'pair-0002.json').write_text('PRIVATE_STALE')
        r = self.invoke([1, 2], expected=3, extra=['--pair-column-counts'], aggregate=False)
        self.assertEqual(r.returncode, 2, r.stderr)
        d = json.loads(r.stdout)
        self.assertTrue(d['partial'])
        self.assertEqual(d['error'], 1); self.assertEqual(d['incomplete'], 1)
        self.assertEqual([p['pair'] for p in d['pair_column_tallies']], ['pair-0001'])

    def test_per_pair_empty_and_unstarted(self):
        for statuses in ([2, 9], []):
            r = self.invoke(statuses, expected=2, extra=['--pair-column-counts'], aggregate=False)
            self.assertEqual(r.returncode, 2, r.stderr)
            d = json.loads(r.stdout)
            self.assertTrue(d['partial']); self.assertEqual(d['pair_column_tallies'], [])

    def test_per_pair_malformed_or_contradictory_report_no_output(self):
        for status, raw in ((1, '{"PRIVATE_SENTINEL":'), (1, None), (0, None)):
            if raw is None:
                self.report(1)
            else:
                (self.root/'pair-0001.json').write_text(raw)
            if status == 1 and raw is None:
                (self.root/'pair-0001.json').unlink()
            r = self.invoke([status], extra=['--pair-column-counts'], aggregate=False)
            self.assertEqual(r.returncode, 2); self.assertEqual(r.stdout, b'')

if __name__ == '__main__':unittest.main()
