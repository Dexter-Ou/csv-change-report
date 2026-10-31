"""Synthetic end-to-end manifest tests; no network or customer data."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / 'evaluation/batch-manifest.py'
spec = importlib.util.spec_from_file_location('batch_manifest', SCRIPT)
manifest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest_module)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / 'data space'
        self.data.mkdir()
        self.before = self.data / '-before $(touch NEVER).csv'
        self.after = self.data / 'after café.csv'
        self.before.write_text('id,value,time\n1,a,x\n', encoding='utf-8')
        self.after.write_text('id,value,time\n1,b,y\n', encoding='utf-8')
        self.manifest = self.data / 'batch.json'
        self.valid = {'version': 1, 'pairs': [{'before': self.before.name,
                       'after': self.after.name, 'key': 'id'}]}

    def write(self, data=None):
        self.manifest.write_text(json.dumps(self.valid if data is None else data), encoding='utf-8')

    def run_manifest(self, name='reports', options=()):
        return subprocess.run([sys.executable, str(SCRIPT), *options, str(self.manifest), name],
                              cwd=self.root, capture_output=True, timeout=20)

    def test_equivalence_and_literal_paths(self):
        self.valid['pairs'] += [dict(self.valid['pairs'][0], after=self.before.name),
                               dict(self.valid['pairs'][0], before='missing.csv'),
                               dict(self.valid['pairs'][0], after=self.before.name)]
        self.write()
        for options in ((), ('--totals',), ('--totals', '--ignore-column', 'time')):
            with self.subTest(options=options):
                n=str(len(options))
                result=self.run_manifest('manifest'+n, options)
                triples=manifest_module.load_manifest(self.manifest)
                direct=subprocess.run(['sh',str(ROOT/'evaluation/batch-review.sh'),*options,'--','direct'+n,*triples],
                                      cwd=self.root,capture_output=True,timeout=20)
                self.assertEqual(result.returncode,2)
                self.assertEqual(result.returncode,direct.returncode)
                for a in (self.root/('manifest'+n)).iterdir():
                    b=self.root/('direct'+n)/a.name
                    self.assertTrue(b.exists(),a.name)
                    self.assertEqual(a.read_bytes(),b.read_bytes(),a.name)
                statuses=(self.root/('manifest'+n)/'status.tsv').read_text()
                self.assertEqual([r.split('\t')[1] for r in statuses.splitlines()[1:]], ['1','0','2','0'])
        self.assertFalse((self.root/'NEVER').exists())
        self.assertFalse((self.data/'NEVER').exists())

    def test_exact_key_and_whitespace(self):
        for i,key in enumerate((' id ', '-id', '識別子', '$(touch NEVER)')):
            with self.subTest(key=key):
                self.before.write_text(key+',value\n1,a\n',encoding='utf-8')
                self.after.write_text(key+',value\n1,b\n',encoding='utf-8')
                self.valid['pairs'][0]['key']=key
                self.write()
                result=self.run_manifest('exact'+str(i))
                self.assertEqual(result.returncode,1,result.stderr)
                report=json.loads((self.root/('exact'+str(i))/'pair-0001.json').read_text())
                self.assertEqual(report['counts']['changed'],1)
                self.assertEqual(manifest_module.load_manifest(self.manifest)[-1],key)

    def test_invalid_schema_creates_no_reports(self):
        cases=[{},[],None,{'version':True,'pairs':self.valid['pairs']},
               {'version':2,'pairs':self.valid['pairs']},dict(self.valid,command='touch NEVER'),
               dict(self.valid,pairs=[]),dict(self.valid,pairs=self.valid['pairs']*101)]
        for field in ('before','after','key'):
            for value in ('',None,False,[], 'x\n', 'x\x00','\ud800'):
                cases.append(dict(self.valid,pairs=[dict(self.valid['pairs'][0],**{field:value})]))
            pair=dict(self.valid['pairs'][0]);del pair[field]
            cases.append(dict(self.valid,pairs=[pair]))
        cases.append(dict(self.valid,pairs=[dict(self.valid['pairs'][0],extra=1)]))
        # Full validation must reject a bad later pair before executing the first.
        cases.append(dict(self.valid,pairs=self.valid['pairs']+[{}]))
        for data in cases:
            with self.subTest(data=data):
                self.manifest.write_text(json.dumps(data),encoding='utf-8')
                result=self.run_manifest()
                self.assertEqual(result.returncode,2)
                self.assertFalse((self.root/'reports').exists())

    def test_invalid_encoding_duplicates_depth_size_and_special_files(self):
        cases=[b'\xff', b'{', b'{"version":1,"version":1,"pairs":[]}',
               b'{"version":1,"pairs":[{"before":"x","before":"y","after":"z","key":"id"}]}',
               b'['*2000+b']'*2000,b' '*65537,
               b'{"version":NaN,"pairs":[]}']
        for raw in cases:
            self.manifest.write_bytes(raw)
            self.assertEqual(self.run_manifest().returncode,2)
            self.assertFalse((self.root/'reports').exists())
        self.manifest.unlink()
        self.assertEqual(self.run_manifest().returncode,2)
        self.manifest.mkdir()
        self.assertEqual(self.run_manifest().returncode,2)
        self.manifest.rmdir()
        import os
        os.mkfifo(self.manifest)
        self.assertEqual(self.run_manifest().returncode,2)
        self.assertFalse((self.root/'reports').exists())

    def test_manifest_limits_and_path_resolution(self):
        self.valid['pairs'] *= 100
        self.write()
        self.assertEqual(len(manifest_module.load_manifest(self.manifest)),300)
        raw=self.manifest.read_bytes()
        self.manifest.write_bytes(raw+b' '*(65536-len(raw)))
        self.assertEqual(len(manifest_module.load_manifest(self.manifest)),300)
        self.manifest.write_bytes(self.manifest.read_bytes()+b' ')
        with self.assertRaises(ValueError):
            manifest_module.load_manifest(self.manifest)
        self.valid['pairs']=self.valid['pairs'][:1]
        self.valid['pairs'][0]['before']='../data space/'+self.before.name
        self.valid['pairs'][0]['after']=str(self.after)
        self.write()
        self.assertEqual(self.run_manifest().returncode,1)
        # A relative manifest argument and a relative output have separate bases.
        result=subprocess.run([sys.executable,str(SCRIPT),'data space/batch.json','relative reports'],
                              cwd=self.root,capture_output=True,timeout=20)
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertTrue((self.root/'relative reports/status.tsv').is_file())

    def test_symlink_base_and_no_expansion(self):
        self.write()
        link=self.root/'linked.json'
        link.symlink_to(self.manifest)
        triples=manifest_module.load_manifest(link)
        self.assertEqual(triples[0],str(self.root/self.before.name))
        self.valid['pairs'][0]['before']='~/literal-$HOME-*.csv'
        self.write()
        self.assertEqual(manifest_module.load_manifest(self.manifest)[0],
                         str(self.data/'~/literal-$HOME-*.csv'))
        self.assertEqual(self.run_manifest().returncode,2)
        self.assertEqual((self.root/'reports/status.tsv').read_text().splitlines()[1].split('\t')[1],'2')

    def test_exit_codes_budget_and_existing_output(self):
        self.write()
        self.assertEqual(self.run_manifest().returncode,1)
        self.assertEqual(self.run_manifest().returncode,2)
        self.assertEqual(self.run_manifest('small',('--max-input-bytes','1')).returncode,2)
        for value in ('0','10485761','bad'):
            self.assertEqual(self.run_manifest('invalid',('--max-input-bytes',value)).returncode,2)
            self.assertFalse((self.root/'invalid').exists())
        self.valid['pairs'][0]['after']=str(self.before)
        self.write()
        self.assertEqual(self.run_manifest('equal').returncode,0)


if __name__=='__main__':
    unittest.main()
