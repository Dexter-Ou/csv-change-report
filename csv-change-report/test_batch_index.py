"""Synthetic offline index acceptance and refusal tests."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / 'evaluation/batch-index.py'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.tags = []
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        for key, value in attrs:
            if key == 'href': self.links.append(value)

class IndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = self.root / 'results café'
        self.before = self.root / 'before.csv'
        self.after = self.root / 'after.csv'
        self.before.write_text('id,value\n1,a\n')
        self.after.write_text('id,value\n1,b\n')
        self.manifest = self.root / 'batch.json'
    def batch(self, kinds):
        self.manifest.write_text(json.dumps({'version':1,'pairs':[
            {'before':'before.csv','after':{'equal':'before.csv','changed':'after.csv','error':'missing.csv'}[k],'key':'id'} for k in kinds]}))
        result = subprocess.run([sys.executable,str(ROOT/'evaluation/automate-batch.py'),str(self.manifest),str(self.out)],capture_output=True,timeout=20)
        self.assertEqual(result.returncode, 2 if 'error' in kinds else 1 if 'changed' in kinds else 0, result.stderr)
    def index(self, expected, status):
        original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.iterdir() if p.is_file()}
        result=subprocess.run([sys.executable,str(SCRIPT),str(self.out),'--expected-pairs',str(expected)],capture_output=True,timeout=5,cwd=self.root)
        self.assertEqual(result.returncode,status,result.stderr)
        for name,digest in original.items(): self.assertEqual(hashlib.sha256((self.out/name).read_bytes()).hexdigest(),digest)
        return result
    def test_three_pair_acceptance(self):
        self.batch(['equal','changed','error']); self.index(3,2)
        text=(self.out/'index.html').read_text(); parser=Links();parser.feed(text)
        for label in ('EQUAL','CHANGED','ERROR — comparison failed','incomplete=0'):self.assertIn(label,text)
        self.assertEqual(parser.links,['pair-0001.json','pair-0001.stderr','pair-0002.json','pair-0002.stderr','pair-0003.stderr'])
        for link in parser.links:self.assertTrue((self.out/link).is_file())
        self.assertFalse(set(parser.tags)&{'script','iframe','img','style'})
        self.index(3,2) # refuses overwrite and preserves bytes
    def test_incomplete_snapshot(self):
        self.batch(['equal','changed','error'])
        p=self.out/'status.tsv';p.write_text('\n'.join(p.read_text().splitlines()[:2])+'\n')
        self.index(3,2);text=(self.out/'index.html').read_text()
        self.assertEqual(text.count('INCOMPLETE — no completed status row'),2)
        self.assertNotIn('pair-0002.json"',text)
    def test_all_equal_and_changed(self):
        self.batch(['equal']);self.index(1,0)
        shutil.rmtree(self.out);self.batch(['changed']);self.index(1,1)
    def test_corrupt_summary_and_missing_diagnostic(self):
        self.batch(['equal']);(self.out/'pair-0001.json').write_text('<script>bad</script>');(self.out/'pair-0001.stderr').unlink()
        self.index(1,2);text=(self.out/'index.html').read_text()
        self.assertIn('missing or invalid summary',text);self.assertIn('diagnostic missing',text);self.assertNotIn('<script>',text)
        self.assertNotIn('href=',text)
    def test_unsafe_table_and_wrong_count(self):
        self.batch(['equal']);self.index(0,2);self.assertFalse((self.out/'index.html').exists())
        p=self.out/'status.tsv';p.write_text(p.read_text().replace('pair-0001.json','../../outside.json'))
        self.index(1,2);self.assertFalse((self.out/'index.html').exists())
    def test_symlinks_refused(self):
        self.batch(['equal']);p=self.out/'pair-0001.json';other=self.root/'other.json';p.rename(other);p.symlink_to(other)
        self.index(1,2);self.assertIn('missing or invalid summary',(self.out/'index.html').read_text())
        (self.out/'index.html').unlink();(self.out/'index.html').symlink_to(self.root/'absent')
        self.index(1,2);self.assertFalse((self.root/'absent').exists())
    def test_size_and_count_limits(self):
        self.batch(['equal']);self.index(101,2);self.assertFalse((self.out/'index.html').exists())
        (self.out/'pair-0001.json').write_bytes(b' ' * 1048577)
        self.index(1,2);self.assertIn('missing or invalid summary',(self.out/'index.html').read_text())
        (self.out/'index.html').unlink();(self.out/'status.tsv').write_bytes(b' ' * 65537)
        self.index(1,2);self.assertFalse((self.out/'index.html').exists())
    def test_truncated_table(self):
        self.batch(['equal']);p=self.out/'status.tsv';p.write_bytes(p.read_bytes()[:-1]);self.index(1,2);self.assertFalse((self.out/'index.html').exists())

if __name__ == '__main__': unittest.main()
