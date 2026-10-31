"""Synthetic byte-budget acceptance tests; run only on the isolated worker."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from csv_change import InputError, MAX_BYTES, compare, load


class InputBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tool = Path(__file__).with_name('csv_change.py')
        self.before = self.root / 'before.csv'
        self.after = self.root / 'after.csv'
        self.before.write_bytes(b'id,x\na,1\n')
        self.after.write_bytes(b'id,x\na,2\n')
        self.originals = [p.read_bytes() for p in (self.before, self.after)]

    def cli(self, *options):
        result = subprocess.run([sys.executable, str(self.tool), str(self.before),
                                 str(self.after), '--key', 'id', *options],
                                capture_output=True, timeout=10)
        self.assertEqual([p.read_bytes() for p in (self.before, self.after)], self.originals)
        return result

    def test_exact_limit_and_default_parity(self):
        default = self.cli('--check')
        exact = self.cli('--max-input-bytes', str(len(self.originals[0])), '--check')
        self.assertEqual((default.returncode, exact.returncode), (1, 1))
        self.assertEqual(exact.stdout, default.stdout)
        report = json.loads(exact.stdout)
        self.assertEqual(report['before_sha256'], hashlib.sha256(self.originals[0]).hexdigest())
        self.assertEqual(report['after_sha256'], hashlib.sha256(self.originals[1]).hexdigest())
        equal = self.root / 'equal.json'
        self.after.write_bytes(self.originals[0]); self.originals[1] = self.originals[0]
        result = self.cli('--max-input-bytes', '9', '--check', '--output', str(equal))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(equal.read_bytes())['counts']['unchanged'], 1)

    def test_one_byte_over_either_input_and_no_output(self):
        for side in (self.before, self.after):
            with self.subTest(side=side.name):
                side.write_bytes(side.read_bytes() + b'\n')
                self.originals = [p.read_bytes() for p in (self.before, self.after)]
                target = self.root / ('new-' + side.name + '.json')
                result = self.cli('--max-input-bytes', '9', '--output', str(target))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b'')
                self.assertEqual(json.loads(result.stderr), {'error': 'input exceeds max input bytes limit'})
                self.assertFalse(target.exists())
                side.write_bytes(side.read_bytes()[:-1])
                self.originals = [p.read_bytes() for p in (self.before, self.after)]

    def test_existing_report_preserved_on_accept_and_refusal(self):
        target = self.root / 'existing.json'; target.write_bytes(b'preserve me')
        for budget in ('9', '8'):
            result = self.cli('--max-input-bytes', budget, '--output', str(target))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(target.read_bytes(), b'preserve me')

    def test_invalid_cli_budgets_are_private_and_do_not_open_inputs(self):
        for value in ('0', '-1', str(MAX_BYTES + 1), '1.5', 'private-sentinel', '9' * 100):
            result = self.cli('--max-input-bytes', value)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b'')
            if value == 'private-sentinel':
                self.assertNotIn(value.encode(), result.stderr)
        with patch('csv_change.Path.open', side_effect=AssertionError('must validate first')):
            for value in (0, -1, MAX_BYTES + 1, True, 9.0, '9'):
                with self.assertRaises(InputError): load(self.before, 'id', value)

    def test_bounded_read_and_ceiling_cannot_be_raised(self):
        stream = io.BytesIO(b'id\na\nTRAILING')
        with patch('csv_change.Path.open') as opened:
            opened.return_value.__enter__.return_value = stream
            with self.assertRaises(InputError): load(self.before, 'id', 5)
            self.assertEqual(stream.tell(), 6)
        with patch('csv_change.Path.open') as opened:
            with self.assertRaises(InputError): load(self.before, 'id', MAX_BYTES + 1)
            opened.assert_not_called()

    def test_multibyte_bom_and_crlf_count_as_bytes(self):
        data = b'\xef\xbb\xbfid,x\r\na,\xc3\xa9\r\n'
        self.before.write_bytes(data); self.after.write_bytes(data)
        self.originals = [data, data]
        accepted = self.cli('--max-input-bytes', str(len(data)), '--check')
        refused = self.cli('--max-input-bytes', str(len(data)-1))
        self.assertEqual(accepted.returncode, 0)
        self.assertEqual(refused.returncode, 2)
        self.assertEqual(json.loads(accepted.stdout)['before_sha256'], hashlib.sha256(data).hexdigest())

    def test_row_and_parser_checks_still_apply(self):
        with patch('csv_change.MAX_ROWS', 0), self.assertRaises(InputError):
            compare(self.before, self.after, 'id', max_input_bytes=9)
        self.before.write_bytes(b'id\na\na\n')
        with self.assertRaises(InputError): load(self.before, 'id', 9)


if __name__ == '__main__': unittest.main()
