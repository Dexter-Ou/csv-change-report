"""Synthetic ignore-column acceptance tests; execute on isolated worker."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from csv_change import compare, InputError, render_text


class IgnoreColumnsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before = self.put('before.csv', 'id,value,updated,nonce\na,keep,old,one\nb,keep,old,one\n')
        self.after = self.put('after.csv', 'nonce,updated,value,id\ntwo,new,keep,a\ntwo,new,keep,b\n')
        self.tool = Path(__file__).with_name('csv_change.py')

    def put(self, name, text):
        p = self.root / name
        p.write_text(text, encoding='utf-8')
        return p

    def cli(self, *flags, after=None, tool=None):
        return subprocess.run([sys.executable, str(tool or self.tool), str(self.before),
                               str(after or self.after), '--key', 'id', *flags],
                              capture_output=True)

    def test_only_selected_fields_are_ignored(self):
        one = compare(self.before, self.after, 'id', ['updated'])
        self.assertEqual(one['counts']['changed'], 2)
        self.assertEqual(one['changed_cells_by_column'], {'value': 0, 'nonce': 2})
        self.assertEqual(one['changed_records'][0]['columns'], ['nonce'])
        both = compare(self.before, self.after, 'id', ['nonce', 'updated', 'nonce'])
        self.assertEqual(both['counts']['changed'], 0)
        self.assertEqual(both['counts']['unchanged'], 2)
        self.assertEqual(both['ignored_columns'], ['updated', 'nonce'])
        self.assertEqual(both['changed_cells_by_column'], {'value': 0})
        self.assertEqual(one['before_sha256'], hashlib.sha256(self.before.read_bytes()).hexdigest())
        self.assertEqual(one['after_sha256'], hashlib.sha256(self.after.read_bytes()).hexdigest())

    def test_real_changes_additions_removals_and_all_nonkeys(self):
        after = self.put('delta.csv', 'id,value,updated,nonce\na,CHANGED,new,two\nc,keep,new,two\n')
        r = compare(self.before, after, 'id', ['updated', 'nonce'])
        self.assertEqual(r['counts'], {'before': 2, 'after': 2, 'added': 1, 'removed': 1, 'changed': 1, 'unchanged': 0})
        self.assertEqual(r['changed_records'][0]['columns'], ['value'])
        all_nonkeys = compare(self.before, after, 'id', ['value', 'updated', 'nonce'])
        self.assertEqual(all_nonkeys['counts']['changed'], 0)
        self.assertEqual(all_nonkeys['counts']['added'], 1)
        self.assertEqual(all_nonkeys['counts']['removed'], 1)
        self.assertEqual(all_nonkeys['changed_cells_by_column'], {})
        self.assertNotIn('CHANGED', json.dumps(r))

    def test_check_stdout_file_and_input_preservation(self):
        original = (self.before.read_bytes(), self.after.read_bytes())
        for fmt in ['json', 'text']:
            base = self.cli('--check', '--format', fmt)
            self.assertEqual(base.returncode, 1)
            flags = ['--check', '--format', fmt, '--ignore-column', 'updated', '--ignore-column', 'nonce']
            r = self.cli(*flags)
            self.assertEqual((r.returncode, r.stderr), (0, b''))
            if fmt == 'json': self.assertEqual(json.loads(r.stdout)['ignored_columns'], ['updated', 'nonce'])
            else: self.assertIn(b'Ignored columns: "updated", "nonce"\n', r.stdout)
            target = self.root / ('report.' + fmt)
            f = self.cli(*flags, '--output', str(target))
            self.assertEqual((f.returncode, f.stdout, f.stderr), (0, b'', b''))
            self.assertEqual(target.read_bytes(), r.stdout)
            again = self.cli(*flags, '--output', str(target))
            self.assertEqual(again.returncode, 2)
            self.assertEqual(target.read_bytes(), r.stdout)
        self.assertEqual(original, (self.before.read_bytes(), self.after.read_bytes()))

    def test_invalid_names_key_schema_and_no_output(self):
        for names, error in [(['id'], 'key column cannot be ignored'),
                             (['UPDATED'], 'ignored column is missing'),
                             (['private synthetic name'], 'ignored column is missing')]:
            flags = [x for name in names for x in ['--ignore-column', name]]
            target = self.root / 'absent.json'
            r = self.cli(*flags, '--output', str(target), '--check')
            self.assertEqual((r.returncode, r.stdout), (2, b''))
            self.assertEqual(json.loads(r.stderr), {'error': error})
            self.assertFalse(target.exists())
        schema = self.put('schema.csv', 'id,value,nonce\na,keep,two\n')
        with self.assertRaisesRegex(InputError, 'column sets differ'):
            compare(self.before, schema, 'id', ['updated'])
        missing_arg = self.cli('--ignore-column')
        self.assertEqual(missing_arg.returncode, 2)

    def test_ignored_data_still_validated(self):
        for text in ['id,value,updated,nonce\na,keep,x,1\na,keep,y,2\n',
                     'id,value,updated,nonce\na,keep,x\n',
                     'id,value,updated,nonce\na,keep,\x00,1\n']:
            invalid = self.put('invalid.csv', text)
            with self.assertRaises(InputError):
                compare(self.before, invalid, 'id', ['updated', 'nonce'])
        empty = self.put('empty.csv', 'id,value,updated,nonce\n')
        self.assertEqual(compare(empty, empty, 'id', ['updated'])['counts']['changed'], 0)

    def test_column_metadata_escapes_control_characters(self):
        before = self.put('quoted-before.csv', 'id,"stamp\n\x1b",value\na,old,keep\n')
        after = self.put('quoted-after.csv', 'id,"stamp\n\x1b",value\na,new,keep\n')
        r = compare(before, after, 'id', ['stamp\n\x1b'])
        text = render_text(r)
        self.assertIn('Ignored columns: "stamp\\n\\u001b"', text)
        self.assertNotIn('\x1b', text)
        self.assertEqual(r['counts']['changed'], 0)



if __name__ == '__main__':
    unittest.main()
