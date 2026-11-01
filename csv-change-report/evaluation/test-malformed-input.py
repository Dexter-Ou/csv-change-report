#!/usr/bin/env python3
"""Synthetic malformed-input regression. Standard library only; keeps temporary reports."""
from pathlib import Path
import json,sys,os,hashlib,subprocess,tempfile
if not __debug__:
 raise SystemExit('Run without -O: regression assertions must be enabled')
p=Path(__file__).resolve().parents[1]
b=Path(tempfile.mkdtemp(prefix='csv-malformed-'));f=b/'fixtures';f.mkdir()
print('Retained test files: '+str(b),file=sys.stderr)
inv=json.loads((p/'READER-BUNDLE-FILES.json').read_text(encoding='utf-8'))['files']
def inventory():
 for n,h in inv.items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
inventory()
valid=b'id,value\n1,ok\n';(f/'valid.csv').write_bytes(valid)
cases={
 'duplicate-key':b'id,value\n1,a\n1,b\n',
 'duplicate-header':b'id,value,value\n1,a,b\n',
 'invalid-utf8':b'id,value\n1,\xff\n',
 'short-row':b'id,value\n1\n',
 'long-row':b'id,value\n1,a,b\n'}
oracle=json.loads((p/"evaluation/malformed-input/oracle.json").read_text(encoding="utf-8"))
commands=[]
def run(label,args,status):
 r=subprocess.run([sys.executable,*map(str,args)],cwd=b,capture_output=True,timeout=45)
 (b/(label+'.stdout')).write_bytes(r.stdout);(b/(label+'.stderr')).write_bytes(r.stderr)
 commands.append({'label':label,'exit_code':r.returncode,'expected':status})
 assert r.returncode==status,(label,r.returncode,r.stderr)
 return r
for name,raw in cases.items():
 diagnostic=oracle[name]
 bad=f/(name+'.csv');bad.write_bytes(raw)
 for side in ['before','after']:
  for mode in ['full','summary']:
   dest=b/(name+'-'+side+'-'+mode+'.json')
   args=[p/'csv_change.py',bad if side=='before' else f/'valid.csv',f/'valid.csv' if side=='before' else bad,'--key','id','--output',dest]
   if mode=='summary':args+=['--summary-only']
   r=run(name+'-'+side+'-'+mode,args,2)
   assert json.loads(r.stderr)=={'error':diagnostic},('diagnostic mismatch',name,diagnostic,r.stderr)
   assert not r.stdout and not dest.exists(),dest
pairs=[{'before':name+'.csv','after':'valid.csv','key':'id'} for name in cases]+[{'before':'valid.csv','after':'valid.csv','key':'id'}]
m=f/'manifest.json';m.write_text(json.dumps({'version':1,'pairs':pairs}))
out=b/'batch';r=run('batch',[p/'evaluation/automate-batch.py',m,out],2)
assert json.loads(r.stdout)=={'version':1,'code':'E_COMPARISON','status':2,'pair_count':6},r.stdout
r=run('totals',[p/'evaluation/batch-totals.py',out/'status.tsv','--expected-pairs','6'],2)
totals=json.loads(r.stdout);assert totals==dict(expected=6,completed=6,equal=1,changed=0,error=5,incomplete=0),totals
for i in range(1,6):
 q=out/('pair-%04d.json'%i);assert not q.exists() or q.stat().st_size==0,q
assert json.loads((out/'pair-0006.json').read_text())['counts']==dict(before=1,after=1,added=0,removed=0,changed=0,unchanged=1)
run('index',[p/'evaluation/batch-index.py',out,'--expected-pairs','6'],2)
html=(out/'index.html').read_text();assert html.count('ERROR')>=5 and 'EQUAL' in html
# Also distinguish duplicate manifest JSON fields from duplicate CSV keys.
d=f/'duplicate-manifest.json';d.write_text('{"version":1,"version":1,"pairs":[]}')
r=run('duplicate-manifest',[p/'evaluation/batch-manifest.py','--validate-only','--json',d],2)
assert json.loads(r.stdout)['code']=='E_DUPLICATE'
run('duplicate-preflight',[p/'evaluation/automate-batch.py',d,b/'must-not-exist'],2)
assert not (b/'must-not-exist').exists()
inventory()
result={'synthetic':True,'uid':os.getuid() if hasattr(os,'getuid') else None,'direct_invalid_cases':20,'batch_totals':totals,'inventory_hashes':len(inv),'source_preserved':True,'commands':commands}
(b/'results.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'results_path':str(b),'result':result},ensure_ascii=False))
