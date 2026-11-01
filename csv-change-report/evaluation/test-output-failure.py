#!/usr/bin/env python3
"""Synthetic Linux output-failure regression; standard library only."""
from pathlib import Path
import os,json,zipfile,subprocess,hashlib,resource,signal,shutil
import sys,tempfile
if not __debug__:
 raise SystemExit('Run without -O: regression assertions must be enabled')
if sys.platform != 'linux' or os.geteuid() == 0:
 raise SystemExit('Requires Linux and a non-root user; do not run with sudo')
p=Path(__file__).resolve().parents[1]
W=Path(tempfile.mkdtemp(prefix='csv-output-failure-'));b=W/'samples';b.mkdir()
print('Retained test files: '+str(W),file=sys.stderr)
oracle=json.loads((p/'evaluation/output-failure/oracle.json').read_text(encoding='utf-8'))
inv=json.loads((p/'READER-BUNDLE-FILES.json').read_text())['files']
def inventory():
 for n,h in inv.items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
inventory()
def demote(limit):
 def child():
  if limit:
   signal.signal(signal.SIGXFSZ,signal.SIG_IGN);resource.setrlimit(resource.RLIMIT_FSIZE,(2048,2048))
 return child
commands=[];checks=[]
def run(label,args,limit=False):
 r=subprocess.run([sys.executable,*map(str,args)],cwd=W,capture_output=True,timeout=60,preexec_fn=demote(limit))
 (b/(label+'.stdout')).write_bytes(r.stdout);(b/(label+'.stderr')).write_bytes(r.stderr)
 commands.append({'label':label,'exit_code':r.returncode,'file_size_limit':2048 if limit else None})
 return r
def check(label,condition):checks.append({'check':label,'passed':bool(condition)})
v=b/'valid.csv';v.write_text('id,value\n1,ok\n');before_hash=hashlib.sha256(v.read_bytes()).hexdigest()
locked=b/'locked';locked.mkdir();locked.chmod(0o555)
existing=b/'existing-dir';existing.mkdir();(existing/'sentinel').write_bytes(b'KEEP DIRECTORY')
sentinel=b/'existing.json';sentinel.write_bytes(b'KEEP FILE')
for mode in ['full','summary']:
 for name,target,diagnostic in [('permission',locked/'report.json',oracle['write']),('directory',existing,oracle['exists']),('existing-file',sentinel,oracle['exists']),('input-collision',v,oracle['collision'])]:
  args=[p/'csv_change.py',v,v,'--key','id','--output',target]
  if mode=='summary':args+=['--summary-only']
  r=run(name+'-'+mode,args)
  check(name+'-'+mode,r.returncode==2 and not r.stdout and json.loads(r.stderr)=={'error':diagnostic})
check('unwritable target absent',not (locked/'report.json').exists())
check('existing file preserved',sentinel.read_bytes()==b'KEEP FILE')
check('directory sentinel preserved',(existing/'sentinel').read_bytes()==b'KEEP DIRECTORY')
check('input preserved',hashlib.sha256(v.read_bytes()).hexdigest()==before_hash)
for name,target in [('locked-parent',locked/'batch'),('existing-dir',existing)]:
 m=b/'small-manifest.json';m.write_text(json.dumps({'version':1,'pairs':[{'before':'valid.csv','after':'valid.csv','key':'id'}]}))
 r=run('automation-'+name,[p/'evaluation/automate-batch.py',m,target]);metadata=json.loads(r.stdout)
 check('automation-'+name,r.returncode==2 and metadata['status']==2 and metadata['code'] in ['E_OUTPUT','E_STATUS'])
check('locked batch absent',not (locked/'batch').exists())
# Deterministic per-process file-size fault, no product modifications or race.
large=b/'large.csv';large.write_text('id,'+','.join('column_%03d'%i for i in range(180))+'\n1,'+','.join('x' for _ in range(180))+'\n')
after=b/'large-after.csv';after.write_text(large.read_text().replace('\n1,'+','.join('x' for _ in range(180)), '\n1,'+','.join('y' for _ in range(180))))
r=run('wide-control',[p/'csv_change.py',large,after,'--key','id','--summary-only','--check']);check('wide control exceeds fault limit',r.returncode==1 and len(r.stdout)>2048)
m=b/'mixed.json';m.write_text(json.dumps({'version':1,'pairs':[{'before':'large.csv','after':'large-after.csv','key':'id'},{'before':'valid.csv','after':'valid.csv','key':'id'}]}))
out=b/'mixed-reports';r=run('mixed-batch',[p/'evaluation/automate-batch.py',m,out],True)
metadata=json.loads(r.stdout);check('mixed returns comparison error',r.returncode==2 and metadata=={'version':1,'code':'E_COMPARISON','status':2,'pair_count':2})
r=run('totals',[p/'evaluation/batch-totals.py',out/'status.tsv','--expected-pairs','2']);totals=json.loads(r.stdout)
check('mixed totals',r.returncode==2 and totals==dict(expected=2,completed=2,equal=1,changed=0,error=1,incomplete=0))
check('valid report remains readable',json.loads((out/'pair-0002.json').read_text())['counts']==dict(before=1,after=1,added=0,removed=0,changed=0,unchanged=1))
check('write fault diagnostic',json.loads((out/'pair-0001.stderr').read_text())=={'error':oracle['write']})
failed=out/'pair-0001.json';partial=failed.stat().st_size if failed.exists() else None
check('failed destination absent',partial is None)
check('temporary siblings absent',not list(out.glob('.csv-change-*')))
status=(out/'status.tsv').read_text()
check('failed report excluded from status',status.splitlines()[1].split('\t')[1:3]==['2','-'])
r=run('index',[p/'evaluation/batch-index.py',out,'--expected-pairs','2'])
html=(out/'index.html').read_text();check('index signals error',r.returncode==2 and 'ERROR' in html and 'EQUAL' in html and 'Unavailable' in html)
inventory();check('inventory preserved',True)
result={'synthetic':True,'platform':'Linux','child_uid':os.geteuid(),'inventory_hashes':len(inv),'checks':checks,'commands':commands,'mixed_totals':totals,'failed_report_bytes':partial,'all_passed':all(x['passed'] for x in checks)}
(W/'results.json').write_text(json.dumps(result,indent=2));shutil.make_archive(str(W/'samples'),'zip',b)
print(json.dumps({'results_path':str(W),'result':result}));assert result['all_passed'], 'output-failure regression failed'
