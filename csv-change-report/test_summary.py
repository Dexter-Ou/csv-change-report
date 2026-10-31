"""Original synthetic summary-mode acceptance tests; run on isolated worker."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from csv_change import compare, render_text

class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.old = self.root/'old.csv'
        self.new = self.root/'new.csv'
        self.old.write_text('id,status,note\na,open,PRIVATE\nb,open,x\nc,done,x\n',encoding='utf8')
        self.new.write_text('note,status,id\nPRIVATE,closed,a\nx,open,d\nx,done,c\n',encoding='utf8')

    def cli(self, *args):
        return subprocess.run([sys.executable,str(Path(__file__).with_name('csv_change.py')),str(self.old),str(self.new),'--key','id',*args],capture_output=True,text=True)

    def test_summary_parity_omission_and_hashes(self):
        for ignores in [(),('status',),('status','note'),('status','status')]:
            for after in [self.old,self.new]:
                with self.subTest(ignores=ignores,after=after.name):
                    full=compare(self.old,after,'id',ignores)
                    summary=compare(self.old,after,'id',ignores,True)
                    self.assertEqual(summary['format_version'],2)
                    self.assertEqual(summary['report_mode'],'summary')
                    self.assertEqual(summary['before_sha256'],hashlib.sha256(self.old.read_bytes()).hexdigest())
                    self.assertEqual(summary['after_sha256'],hashlib.sha256(after.read_bytes()).hexdigest())
                    for field in ('added_after_records','removed_before_records','changed_records'):
                        self.assertNotIn(field,summary)
                        del full[field]
                    full.update(format_version=2,report_mode='summary')
                    self.assertEqual(summary,full)
                    self.assertNotIn('PRIVATE',json.dumps(summary))
                    text=render_text(summary)
                    self.assertIn('record details omitted',text)
                    self.assertNotIn('before 1 ->',text)
                    self.assertNotIn('Added after records:',text)

    def test_cli_formats_check_and_output(self):
        for fmt in ['json','text']:
            for check in [[],['--check']]:
                for ignores in [[],['--ignore-column','status']]:
                    args=['--format',fmt,*check,*ignores]
                    full=self.cli(*args)
                    summary=self.cli(*args,'--summary-only')
                    self.assertEqual(summary.returncode,full.returncode)
                    self.assertEqual(summary.stderr,'')
                    self.assertEqual(summary.returncode,int(bool(check)))
                    target=self.root/('report-'+fmt+str(len(check))+str(len(ignores)))
                    saved=self.cli(*args,'--summary-only','--output',str(target))
                    self.assertEqual(saved.returncode,summary.returncode)
                    self.assertEqual(saved.stdout,'')
                    self.assertEqual(target.read_text(),summary.stdout)
                    refused=self.cli(*args,'--summary-only','--output',str(target))
                    self.assertEqual(refused.returncode,2)
                    self.assertEqual(target.read_text(),summary.stdout)

    def test_invalid_summary_preserves_output(self):
        self.new.write_text('id,status,note\na,open,x\na,done,x\n')
        output=self.root/'sentinel';output.write_bytes(b'sentinel')
        r=self.cli('--summary-only','--output',str(output))
        self.assertEqual(r.returncode,2)
        self.assertEqual(r.stdout,'')
        self.assertEqual(output.read_bytes(),b'sentinel')

    def test_large_diff_summary_size(self):
        self.old.write_text('id,status\n'+''.join(f'{i},old\n' for i in range(10000)))
        self.new.write_text('id,status\n'+''.join(f'{i},new\n' for i in range(10000)))
        full=self.cli('--check');summary=self.cli('--check','--summary-only')
        self.assertEqual((full.returncode,summary.returncode),(1,1))
        f,s=json.loads(full.stdout),json.loads(summary.stdout)
        self.assertEqual(s['counts'],{'before':10000,'after':10000,'added':0,'removed':0,'changed':10000,'unchanged':0})
        self.assertEqual(s['changed_cells_by_column'],{'status':10000})
        self.assertEqual(f['counts'],s['counts'])
        self.assertLess(len(summary.stdout),len(full.stdout)//100)

if __name__=='__main__': unittest.main()
