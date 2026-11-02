#!/usr/bin/env python3
"""Optional trusted-synthetic-file Linux process-group termination experiment."""
from pathlib import Path
import os,sys,hashlib,json,subprocess,time,signal,platform
if not sys.platform.startswith('linux') or not Path('/proc').is_dir():
 raise SystemExit('Linux with /proc required; no files created')
if len(sys.argv)!=2:
 raise SystemExit('Usage: python3 terminate-demo.py NEW_OUTPUT_DIRECTORY')
base=Path(sys.argv[1]).absolute()
try:
 base.mkdir()
except FileExistsError:
 print('Output path already exists; choose a new directory.',file=sys.stderr)
 raise SystemExit(2)
product=Path(__file__).resolve().parents[2]
def hashes(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
source_hashes={str(p.relative_to(product)):hashlib.sha256(p.read_bytes()).hexdigest() for p in product.rglob('*.py') if '__pycache__' not in p.parts}
fixtures=base/'fixtures'; fixtures.mkdir()
for name,changed in [('before.csv',False),('after.csv',True)]:
 with (fixtures/name).open('x') as f:
  f.write('id,value\n')
  for i in range(10000): f.write(str(i)+','+('changed' if changed and i==9999 else 'x'*900)+'\n')
pairs=[{'before':'before.csv','after':'before.csv' if i%2==0 else 'after.csv','key':'id'} for i in range(10)]
manifest=fixtures/'manifest.json';manifest.write_text(json.dumps({'version':1,'pairs':pairs}))
inputs=hashes(fixtures)
stopped=base/'terminated';fresh=base/'fresh'
def command(out): return [sys.executable,str(product/'evaluation/batch-manifest.py'),'--totals',str(manifest),str(out)]
def run(label,args,expected):
 r=subprocess.run(args,capture_output=True,timeout=120)
 (base/(label+'.stdout')).write_bytes(r.stdout);(base/(label+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==expected,(label,r.returncode,r.stderr.decode())
 return r
p=None
with (base/'terminated-process.stdout').open('xb') as out,(base/'terminated-process.stderr').open('xb') as err:
 p=subprocess.Popen(command(stopped),stdout=out,stderr=err,start_new_session=True)
 try:
  deadline=time.monotonic()+50
  while time.monotonic()<deadline:
   table=stopped/'status.tsv'
   if table.exists() and len(table.read_bytes().splitlines())>=2 and (stopped/'pair-0002.stdout').exists(): break
   assert p.poll() is None,'batch completed before termination'
   time.sleep(.005)
  else: raise AssertionError('termination trigger timed out')
  os.killpg(p.pid,signal.SIGTERM)
  rc=p.wait(timeout=10)
  assert rc==-signal.SIGTERM,rc
 finally:
  try: os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError: pass
  p.wait()
# Verify all remaining process-group members are zombies (no executing writers).
active=[]
for proc in Path('/proc').iterdir():
 if proc.name.isdigit():
  try:
   fields=(proc/'stat').read_text().rsplit(')',1)[1].split()
   if int(fields[2])==p.pid and fields[0]!='Z': active.append(proc.name)
  except (FileNotFoundError,ProcessLookupError,PermissionError): pass
assert not active,('process group still executing; preserve output and investigate',active)
saved=hashes(stopped)
assert not (stopped/'totals.json').exists()
r=run('stopped-totals',[sys.executable,str(product/'evaluation/batch-totals.py'),str(stopped/'status.tsv'),'--expected-pairs','10','--row-counts'],2)
totals=json.loads(r.stdout);assert 1<=totals['completed']<10 and totals['incomplete']==10-totals['completed'] and totals['partial'] is True,totals
run('stopped-index',[sys.executable,str(product/'evaluation/batch-index.py'),str(stopped),'--expected-pairs','10'],2)
assert 'INCOMPLETE' in (stopped/'index.html').read_text()
assert all(hashes(stopped)[k]==v for k,v in saved.items())
saved=hashes(stopped)
run('occupied-refusal',command(stopped),2)
assert hashes(stopped)==saved
run('fresh-rerun',command(fresh),1)
new=json.loads((fresh/'totals.json').read_text())
assert new['completed']==10 and new['equal']==5 and new['changed']==5 and new['incomplete']==0 and new['partial'] is False,new
run('fresh-index',[sys.executable,str(product/'evaluation/batch-index.py'),str(fresh),'--expected-pairs','10'],1)
assert hashes(stopped)==saved and hashes(fixtures)==inputs and {str(p.relative_to(product)):hashlib.sha256(p.read_bytes()).hexdigest() for p in product.rglob('*.py') if '__pycache__' not in p.parts}==source_hashes
result={'platform':platform.platform(),'python':platform.python_version(),'uid':os.getuid(),'signal':'SIGTERM to own process group; final SIGKILL ensures no surviving writers','terminated_returncode':rc,'active_group_members':active,'stopped_totals':totals,'fresh_totals':new,'preserved_stopped_files':saved,'source_file_count':len(source_hashes),'source_preserved':True,'inputs_preserved':True,'limits':'Synthetic Linux process termination only, not power loss, fsync durability, concurrency or market validation.'}
(base/'test-results.json').write_text(json.dumps(result,indent=2))
print('PASS: terminated batch, incomplete snapshot, occupied refusal, fresh recovery; see '+str(base/'test-results.json'))
