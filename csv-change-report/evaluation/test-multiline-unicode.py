#!/usr/bin/env python3
"""Synthetic multiline/Unicode regression; stdlib only, writes to a fresh temp directory.
Run from any directory: python3 evaluation/test-multiline-unicode.py
Expected exit: 0. Keeps generated reports and prints their temporary path.
Do not run with Python -O, which disables the regression assertions.
"""
from pathlib import Path
import os,sys,json,zipfile,subprocess,hashlib,csv,io
from html.parser import HTMLParser
import tempfile
r=Path(__file__).resolve().parents[1]
os.chdir(r)
b=Path(tempfile.mkdtemp(prefix='csv-multiline-'))
inv=json.loads(Path('READER-BUNDLE-FILES.json').read_text())['files']
for p,h in inv.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
f=b/'fixtures';f.mkdir()
source=r/'evaluation'/'multiline-unicode'
import shutil
for p in source.iterdir():
 if p.is_file():shutil.copyfile(p,f/p.name)
oracle=json.loads((f/'oracle.json').read_text())
def run(label,args,status):
 q=subprocess.run([sys.executable,*map(str,args)],capture_output=True,timeout=45)
 (b/(label+'.stdout')).write_bytes(q.stdout);(b/(label+'.stderr')).write_bytes(q.stderr)
 assert q.returncode==status,(label,q.returncode,q.stderr)
 return q
results=[]
for ending in ['LF','CRLF']:
 a=f/('before-'+ending+'.csv');z=f/('after-'+ending+'.csv')
 assert len(list(csv.reader(io.StringIO(a.read_text(),newline=''))))==5
 q=run('detail-'+ending,['csv_change.py',a,z,'--key','識別子'],0);report=json.loads(q.stdout)
 for k,v in oracle.items():assert report[k]==v,(ending,k,report[k],v)
 assert report['before_sha256']==hashlib.sha256(a.read_bytes()).hexdigest()
 assert report['after_sha256']==hashlib.sha256(z.read_bytes()).hexdigest()
 manifest=f/('manifest-'+ending+'.json');manifest.write_text(json.dumps({'version':1,'pairs':[{'before':a.name,'after':z.name,'key':'識別子'},{'before':a.name,'after':a.name,'key':'識別子'}]}))
 out=b/('batch-'+ending)
 run('batch-'+ending,['evaluation/automate-batch.py',manifest,out],1)
 run('index-'+ending,['evaluation/batch-index.py',out,'--expected-pairs','2'],1)
 summary=json.loads((out/'pair-0001.json').read_text());assert summary['counts']==oracle['counts']
 equal=json.loads((out/'pair-0002.json').read_text());assert equal['counts']==dict(before=4,after=4,added=0,removed=0,changed=0,unchanged=4)
 h=(out/'index.html').read_text();assert 'CHANGED' in h and 'EQUAL' in h and 'Unavailable' not in h
 class Links(HTMLParser):
  def handle_starttag(self,tag,attrs):
   for k,v in attrs:
    if k=='href':assert (out/v).is_file(),v
 Links().feed(h)
 results.append(dict(line_endings=ending,detail_matches_oracle=True,batch_status=1,index_status=1,links_resolve=True))
for p,h in inv.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
result=dict(uid=os.getuid(),synthetic=True,inventory_hashes=len(inv),variants=results,counts=oracle['counts'],source_preserved=True,browser_tested=False)
(b/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
with zipfile.ZipFile(b/'samples.zip','w',zipfile.ZIP_DEFLATED) as z:
 for directory in [f,b/'batch-LF',b/'batch-CRLF']:
  for p in directory.rglob('*'):
   if p.is_file():z.write(p,p.relative_to(b))
print(json.dumps(dict(result, output_directory=str(b))))
