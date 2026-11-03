"""Synthetic compound-key CLI and API regressions."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from csv_change import compare, InputError, load


class CompositeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.before = self.root / 'before.csv'
        self.after = self.root / 'after.csv'
        self.before.write_text('tenant,sku,status\na|b,c,old\na,b|c,same\na,c,old\n')
        self.after.write_text('status,sku,tenant\nsame,b|c,a\nnew,c,a|b\nnew,c,added\n')
        # Neither individual column uniquely identifies every before row.
        self.assertEqual(len({'a|b', 'a', 'a'}), 2)
        self.assertEqual(len({'c', 'b|c', 'c'}), 2)
        self.tool = Path(__file__).with_name('csv_change.py')

    def cli(self, *args):
        return subprocess.run([sys.executable, str(self.tool), str(self.before),
                               str(self.after), *args], capture_output=True, text=True)

    def test_tuple_identity_and_report_oracle(self):
        r = compare(self.before, self.after, ['tenant', 'sku'])
        self.assertEqual(r['counts'], dict(before=3, after=3, added=1, removed=1,
                                           changed=1, unchanged=1))
        self.assertEqual(r['changed_records'], [dict(before_record=1, after_record=2,
                                                    columns=['status'])])
        self.assertEqual(r['added_after_records'], [3])
        self.assertEqual(r['removed_before_records'], [3])
        self.assertEqual(r['changed_cells_by_column'], {'status': 1})
        self.assertNotIn('a|b', json.dumps(r))
        self.assertNotIn('same', json.dumps(r))

    def test_cli_check_output_and_no_clobber(self):
        snapshots = self.before.read_bytes(), self.after.read_bytes()
        out = self.root / 'report.json'
        args = ['--key', 'tenant', '--key', 'sku', '--check', '--output', str(out)]
        r = self.cli(*args)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (1, '', ''))
        expected = compare(self.before, self.after, ['tenant', 'sku'])
        self.assertEqual(json.loads(out.read_text()), expected)
        original = out.read_bytes()
        self.assertEqual(self.cli(*args).returncode, 2)
        self.assertEqual(out.read_bytes(), original)
        self.assertEqual((self.before.read_bytes(), self.after.read_bytes()), snapshots)

    def test_cli_text_and_summary(self):
        r = self.cli('--key', 'tenant', '--key', 'sku', '--format', 'text', '--check')
        self.assertEqual((r.returncode, r.stderr), (1, ''))
        self.assertIn('changed 1, unchanged 1', r.stdout)
        r = self.cli('--key', 'tenant', '--key', 'sku', '--summary-only')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)['counts']['changed'], 1)
        self.assertNotIn('changed_records', json.loads(r.stdout))

    def test_invalid_components_refuse_output_without_values(self):
        for text in ['tenant,sku,status\na,x,one\na,x,two\n',
                     'tenant,sku,status\na, ,one\n']:
            with self.subTest(text=text):
                self.before.write_text(text)
                out = self.root / 'invalid.json'
                r = self.cli('--key', 'tenant', '--key', 'sku', '--output', str(out))
                self.assertEqual((r.returncode, r.stdout, out.exists()), (2, '', False))
                self.assertNotIn('one', r.stderr)
                self.assertNotIn(str(self.before), r.stderr)

    def test_key_configuration_failures(self):
        for keys in [[], ['tenant', 'tenant'], ['tenant', 'absent'], ['tenant', ' ']]:
            with self.subTest(keys=keys), self.assertRaises(InputError):
                compare(self.before, self.after, keys)
        for name in ['tenant', 'sku']:
            with self.subTest(ignored=name), self.assertRaises(InputError):
                compare(self.before, self.after, ['tenant', 'sku'], [name])
        r = self.cli('--key', 'tenant', '--key', 'tenant')
        self.assertEqual((r.returncode, r.stdout), (2, ''))

    def test_single_key_api_compatibility(self):
        self.before.write_text('id,value\na,one\nb,two\n')
        self.after.write_text('id,value\na,three\nb,two\n')
        self.assertEqual(compare(self.before, self.after, 'id'),
                         compare(self.before, self.after, ['id']))
        self.assertIn('a', load(self.before, 'id')[1])
        self.assertEqual(self.cli('--key', 'id', '--check').returncode, 1)


if __name__ == '__main__':
    unittest.main()
