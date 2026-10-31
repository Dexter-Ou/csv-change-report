"""Synthetic shell helper journeys; run on isolated worker."""
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parent / 'evaluation' / 'batch-review.sh'

class BatchBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.old = self.root / 'before.csv'
        self.new = self.root / 'after.csv'
        self.old.write_bytes(b'id,x\na,1\n')
        self.new.write_bytes(b'id,x\na,2\n')
        self.originals = {p.name:p.read_bytes() for p in [self.old,self.new]}

    def run_batch(self, name, budget=None, pairs=None):
        args = ['sh',str(HELPER)]
        if budget is not None: args += ['--max-input-bytes',budget]
        args += [name] + (pairs or [str(self.old),str(self.new),'id'])
        result = subprocess.run(args,cwd=self.root,capture_output=True,timeout=20)
        self.assertEqual(self.originals,{p.name:p.read_bytes() for p in [self.old,self.new]})
        return result

    def snapshot(self, directory):
        return {str(p.relative_to(directory)):p.read_bytes() for p in directory.rglob('*') if p.is_file()}

    def test_legacy_and_exact_limit_identical(self):
        self.assertEqual(self.run_batch('legacy').returncode,1)
        self.assertEqual(self.run_batch('custom','9').returncode,1)
        self.assertEqual(self.snapshot(self.root/'legacy'),self.snapshot(self.root/'custom'))

    def test_over_limit_either_side_no_report(self):
        for side in ['old','new']:
            target = self.old if side == 'old' else self.new
            target.write_bytes(b'id,x\na,11\n')
            self.originals[target.name] = target.read_bytes()
            name = 'over-'+side
            self.assertEqual(self.run_batch(name,'9').returncode,2)
            self.assertFalse((self.root/name/'pair-0001.json').exists())
            self.assertIn('pair-0001\t2\t-',(self.root/name/'status.tsv').read_text())
            target.write_bytes(b'id,x\na,1\n' if side == 'old' else b'id,x\na,2\n')
            self.originals[target.name] = target.read_bytes()

    def test_invalid_before_directory_creation_and_no_value_echo(self):
        for i,value in enumerate(['','0','01','-1','+9','1.5','10485761','9'*100,'SYNTHETIC_VALUE']):
            name = 'invalid-'+str(i)
            result = self.run_batch(name,value)
            self.assertEqual(result.returncode,2)
            self.assertFalse((self.root/name).exists())
            self.assertNotIn(b'SYNTHETIC_VALUE',result.stdout+result.stderr)

    def test_missing_budget_and_incomplete_triples(self):
        for args in [['--max-input-bytes'],['--max-input-bytes','9','unused',str(self.old)]]:
            r = subprocess.run(['sh',str(HELPER)]+args,cwd=self.root,capture_output=True)
            self.assertEqual(r.returncode,2)
            self.assertFalse((self.root/'unused').exists())

    def test_continue_after_failure_and_preserve_existing(self):
        big = self.root/'big.csv'
        big.write_bytes(b'id,x\na,111\n')
        pairs = [str(big),str(self.new),'id',str(self.old),str(self.new),'id',str(self.old),str(self.old),'id']
        self.assertEqual(self.run_batch('mixed','9',pairs).returncode,2)
        directory = self.root/'mixed'
        self.assertEqual([line.split('\t')[1] for line in (directory/'status.tsv').read_text().splitlines()[1:]],['2','1','0'])
        before = self.snapshot(directory)
        self.assertEqual(self.run_batch('mixed','9',pairs).returncode,2)
        self.assertEqual(before,self.snapshot(directory))
        self.assertEqual(big.read_bytes(),b'id,x\na,111\n')
        self.assertEqual(self.run_batch('fresh','9').returncode,1)

    def test_spaced_and_dash_directory(self):
        for name in ['reports with spaces','-reports']:
            self.assertEqual(self.run_batch(name,'9').returncode,1)
            self.assertTrue((self.root/name/'pair-0001.json').exists())
