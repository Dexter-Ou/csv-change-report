"""Regression checks for summary validation before successful batch rows."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from csv_change import compare

spec = importlib.util.spec_from_file_location('report_schema', Path(__file__).parent / 'evaluation/report_schema.py')
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)


class BatchReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.before = self.root / 'before.csv'
        self.after = self.root / 'after.csv'
        self.before.write_text('id,value,time\n1,a,x\n')
        self.after.write_text('id,value,time\n1,b,y\n')
        self.report = compare(self.before, self.after, 'id', summary_only=True)
        self.path = self.root / 'report.json'

    def validate(self, report, status='1'):
        self.path.write_text(json.dumps(report))
        return schema.validate_summary(self.path, status)

    def test_real_summaries(self):
        for ignored in ((), ('time',), ('time', 'value')):
            with self.subTest(ignored=ignored):
                report = compare(self.before, self.after, 'id', ignored, summary_only=True)
                self.validate(report, '0' if len(ignored) == 2 else '1')
        self.after.write_text('id,value,time\n')
        self.validate(compare(self.before, self.after, 'id', summary_only=True))
        self.before.write_text('id,value,time\n')
        self.validate(compare(self.before, self.after, 'id', summary_only=True), '0')

    def test_missing_or_extra_fields(self):
        for field in self.report:
            with self.subTest(field=field):
                report = copy.deepcopy(self.report)
                del report[field]
                with self.assertRaises(ValueError):
                    self.validate(report)
        with self.assertRaises(ValueError):
            self.validate(dict(self.report, changed_records=[]))

    def test_count_types_and_accounting(self):
        for value in (-1, True, 1.0, '1', None):
            with self.subTest(value=value):
                report = copy.deepcopy(self.report)
                report['counts']['changed'] = value
                with self.assertRaises(ValueError):
                    self.validate(report)
        report = copy.deepcopy(self.report)
        report['counts']['before'] = 12
        with self.assertRaises(ValueError):
            self.validate(report)

    def test_column_and_ignore_consistency(self):
        for columns in ({}, {'value': 2}, {'value': True}, {'value': -1}, []):
            with self.subTest(columns=columns):
                with self.assertRaises(ValueError):
                    self.validate(dict(self.report, changed_cells_by_column=columns))
        for ignored in (['value'], ['unused', 'unused'], [True], 'time'):
            with self.subTest(ignored=ignored):
                with self.assertRaises(ValueError):
                    self.validate(dict(self.report, ignored_columns=ignored))

    def test_status_and_metadata(self):
        with self.assertRaises(ValueError):
            self.validate(self.report, '0')
        for field, value in [('format_version', True), ('format_version', 1),
                             ('report_mode', 'full'), ('tool_version', ''),
                             ('before_sha256', 'bad'), ('after_sha256', None)]:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    self.validate(dict(self.report, **{field: value}))

    def test_duplicate_json_field(self):
        self.path.write_text(json.dumps(self.report).replace('"counts":', '"counts": {}, "counts":', 1))
        with self.assertRaises(ValueError):
            schema.validate_summary(self.path, '1')
