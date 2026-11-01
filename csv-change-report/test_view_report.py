"""Synthetic saved-report journeys and rejection/security cases."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import view_report

ROOT = Path(__file__).resolve().parent


class Tags(HTMLParser):
    def __init__(self):
        super().__init__(); self.tags = []; self.text = []; self.cells = []; self.in_cell = False
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag == 'td': self.in_cell = True
    def handle_endtag(self, tag):
        if tag == 'td': self.in_cell = False
    def handle_data(self, data):
        self.text.append(data)
        if self.in_cell: self.cells.append(data)


class ViewerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.report = json.loads((ROOT / 'examples/expected-report.json').read_text())

    def run_view(self, raw, target='view.html', extra=()):
        source = self.work / 'saved.json'; source.write_text(raw)
        result = subprocess.run([sys.executable, str(ROOT / 'view_report.py'), str(source), '--output', str(self.work / target), *extra], capture_output=True, text=True)
        return result, self.work / target

    def test_fresh_comparator_journeys(self):
        for label, args in [('details', []), ('summary', ['--summary-only']), ('ignored', ['--ignore-column', 'status'])]:
            with self.subTest(label=label):
                report = self.work / (label + '.json')
                result = subprocess.run([sys.executable, str(ROOT / 'csv_change.py'), str(ROOT / 'examples/before.csv'), str(ROOT / 'examples/after.csv'), '--key', 'id', '--output', str(report), *args], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                result, out = self.run_view(report.read_text(), label + '.html')
                self.assertEqual(result.returncode, 0, result.stderr)
                parsed = Tags(); parsed.feed(out.read_text())
                self.assertIn(('title', {}), parsed.tags)
                self.assertIn('Record counts', parsed.text)
                saved = json.loads(report.read_text())
                expected = [str(v) for pair in saved['counts'].items() for v in pair]
                self.assertEqual(parsed.cells[:12], expected)
                self.assertIn(saved['before_sha256'], parsed.cells)
                self.assertIn(saved['after_sha256'], parsed.cells)
                if label == 'details':
                    self.assertIn(['1', '1', '["status"]'], [parsed.cells[i:i+3] for i in range(len(parsed.cells)-2)])
                if label == 'ignored': self.assertIn('Ignored columns', parsed.text)
                self.assertIn('Summary only:', out.read_text()) if label == 'summary' else self.assertIn('1-based data records', out.read_text())

    def test_escaping_and_no_active_content(self):
        r = copy.deepcopy(self.report)
        hostile = '</td><script>alert(1)</script><img src="https://example.invalid/">'
        r['changed_cells_by_column'][hostile] = r['changed_cells_by_column'].pop('status')
        r['changed_records'][0]['columns'] = [hostile]
        r['tool_version'] = hostile
        html = view_report.render(r); parsed = Tags(); parsed.feed(html)
        self.assertNotIn('script', [t for t, _ in parsed.tags])
        self.assertNotIn('img', [t for t, _ in parsed.tags])
        self.assertFalse(any(k in ('src', 'href', 'onclick') for _, attrs in parsed.tags for k in attrs))
        self.assertIn(hostile, parsed.text)
        self.assertIn('Content-Security-Policy', html)

    def test_inconsistent_and_unsupported_refused_before_output(self):
        cases = []
        for field, value in [('format_version', True), ('format_version', 3), ('counts', {'before': 1}), ('changed_cells_by_column', {'status': 0}), ('before_sha256', 'bad'), ('added_after_records', [True]), ('added_after_records', [4]), ('removed_before_records', [1])]:
            r = copy.deepcopy(self.report); r[field] = value; cases.append(r)
        r = copy.deepcopy(self.report); r['counts']['added'] = True; cases.append(r)
        r = copy.deepcopy(self.report); r['changed_records'][0]['columns'] = ['absent']; cases.append(r)
        r = copy.deepcopy(self.report); r['counts']['changed'] = 2; cases.append(r)
        r = copy.deepcopy(self.report); r['ignored_columns'] = ['status']; cases.append(r)
        cases.extend([[], {'pairs': []}])
        for i, r in enumerate(cases):
            with self.subTest(case=i):
                result, out = self.run_view(json.dumps(r), f'bad-{i}.html')
                self.assertEqual(result.returncode, 2); self.assertFalse(out.exists())
        for i, raw in enumerate(['{', '{"counts":{},"counts":{}}', '[]', 'null', '[' * 2000]):
            result, out = self.run_view(raw, f'malformed-{i}.html')
            self.assertEqual(result.returncode, 2); self.assertFalse(out.exists())

    def test_existing_output_and_input_preserved(self):
        target = self.work / 'occupied.html'; target.write_bytes(b'keep me')
        result, _ = self.run_view(json.dumps(self.report), target.name)
        self.assertEqual(result.returncode, 2); self.assertEqual(target.read_bytes(), b'keep me')
        result, _ = self.run_view(json.dumps(self.report), 'saved.json')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads((self.work / 'saved.json').read_text()), self.report)

    def test_equal_report_and_omitted_summary(self):
        r = copy.deepcopy(self.report)
        r['counts'] = dict(before=3, after=3, added=0, removed=0, changed=0, unchanged=3)
        r['added_after_records'] = []; r['removed_before_records'] = []; r['changed_records'] = []
        r['changed_cells_by_column'] = {'status': 0, 'name': 0}
        self.assertIn('<p>None</p>', view_report.render(r))
        for name in ('added_after_records', 'removed_before_records', 'changed_records'): del r[name]
        r['format_version'] = 2; r['report_mode'] = 'summary'
        html = view_report.render(r)
        self.assertIn('Zero details must not be inferred.', html)
        self.assertNotIn('<p>None</p>', html)

    def test_counts_only_preserves_metadata_and_refuses_collision(self):
        raw = json.dumps(self.report)
        result, out = self.run_view(raw, extra=('--counts-only',))
        self.assertEqual(result.returncode, 0, result.stderr)
        html = out.read_text(); parsed = Tags(); parsed.feed(html)
        default = Tags(); default.feed(view_report.render(self.report))
        self.assertEqual(parsed.cells[:12], default.cells[:12])
        for pair in self.report['changed_cells_by_column'].items():
            self.assertIn(str(pair[0]), parsed.cells)
            self.assertIn(str(pair[1]), parsed.cells)
        for name in ('before_sha256', 'after_sha256'):
            self.assertIn(self.report[name], parsed.cells)
        self.assertIn('Counts-only view:', html)
        self.assertIn('remain in the saved detailed JSON', html)
        self.assertNotIn('<h3>Changed records</h3>', html)
        before = out.read_bytes()
        result, _ = self.run_view(raw, extra=('--counts-only',))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(out.read_bytes(), before)
        self.assertEqual((self.work / 'saved.json').read_text(), raw)
        bad = copy.deepcopy(self.report); bad['changed_records'][0]['before_record'] = 0
        result, invalid = self.run_view(json.dumps(bad), 'invalid-counts.html', ('--counts-only',))
        self.assertEqual(result.returncode, 2); self.assertFalse(invalid.exists())
        summary = copy.deepcopy(self.report)
        for name in ('added_after_records', 'removed_before_records', 'changed_records'): del summary[name]
        summary.update(format_version=2, report_mode='summary')
        html = view_report.render(summary, counts_only=True)
        self.assertIn('Summary only:', html); self.assertNotIn('Counts-only view:', html)

    def test_size_limit_and_missing_input(self):
        result, out = self.run_view(' ' * (view_report.MAX_BYTES + 1))
        self.assertEqual(result.returncode, 2); self.assertFalse(out.exists())
        result = subprocess.run([sys.executable, str(ROOT / 'view_report.py'), str(self.work / 'missing.json'), '--output', str(out)], capture_output=True)
        self.assertEqual(result.returncode, 2); self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
