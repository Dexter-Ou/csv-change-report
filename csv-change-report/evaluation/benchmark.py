from pathlib import Path
import csv,hashlib,json,os,platform,subprocess,sys,time,zipfile
import argparse
if sys.platform != 'linux' or not hasattr(os, 'wait4'):
 raise SystemExit('This optional benchmark requires Linux with os.wait4.')
if not __debug__:
 raise SystemExit('Run without -O: benchmark verification uses assertions.')
parser=argparse.ArgumentParser(description='Run 18 synthetic 50,000-record comparisons; no network.')
parser.add_argument('output_directory',type=Path,help='new directory in a trusted local parent; must not exist')
args=parser.parse_args()
p=Path(__file__).resolve().parents[1]
h=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
inv=json.loads((p/'READER-BUNDLE-FILES.json').read_text())
for n,v in inv['files'].items():assert h(p/n)==v,n
work=args.output_directory.resolve()
work.mkdir()
header=['id','status','note','amount']
def row(i,changed=False):return [str(i),'new' if changed else 'old','synthetic, note\nline' if i%100==0 else 'synthetic',str(i%1000)]
def write(name,rows):
 path=work/name
 with path.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(header);w.writerows(rows)
 assert path.stat().st_size<10485760
 return path
before=write('before.csv',(row(i) for i in range(50000)))
allchange=write('all-change.csv',(row(i,True) for i in range(50000)))
mixed=write('mixed.csv',(row(i,1000<=i<11000) for i in reversed(range(1000,51000))))
inputs={x.name:{'sha256':h(x),'bytes':x.stat().st_size,'records':50000,'data_cells':200000} for x in [before,allchange,mixed]}
results=[]
for scenario,after,counts,tally in [
 ('equal',before,dict(before=50000,after=50000,added=0,removed=0,changed=0,unchanged=50000),0),
 ('mixed',mixed,dict(before=50000,after=50000,added=1000,removed=1000,changed=10000,unchanged=39000),10000),
 ('all-change',allchange,dict(before=50000,after=50000,added=0,removed=0,changed=50000,unchanged=0),50000)]:
 for mode in ['full','summary']:
  for repeat in range(3):
   out=work/f'{scenario}-{mode}-{repeat}.json';err=out.with_suffix('.stderr')
   cmd=[sys.executable,str(p/'csv_change.py'),str(before),str(after),'--key','id','--check']
   if mode=='summary':cmd+=['--summary-only']
   start=time.monotonic()
   with out.open('wb') as of,err.open('wb') as ef:
    proc=subprocess.Popen(cmd,stdout=of,stderr=ef)
    pid,status,usage=os.wait4(proc.pid,0);proc.returncode=os.waitstatus_to_exitcode(status)
   elapsed=time.monotonic()-start
   assert proc.returncode==int(scenario!='equal'),(scenario,proc.returncode)
   assert err.read_bytes()==b''
   d=json.loads(out.read_text());assert d['counts']==counts,d['counts']
   assert d['changed_cells_by_column']=={'status':tally,'note':0,'amount':0}
   assert d['before_sha256']==inputs[before.name]['sha256']
   assert d['after_sha256']==inputs[after.name]['sha256']
   if mode=='full':
    if scenario=='mixed':
     assert d['added_after_records']==list(range(1,1001))
     assert d['removed_before_records']==list(range(1,1001))
     assert d['changed_records']==[{'before_record':i+1,'after_record':51000-i,'columns':['status']} for i in range(1000,11000)]
    elif scenario=='all-change':assert d['changed_records']==[{'before_record':i+1,'after_record':i+1,'columns':['status']} for i in range(50000)]
    else:assert d['changed_records']==[]
   else:
    assert d['report_mode']=='summary'
    assert not {'changed_records','added_after_records','removed_before_records'}&d.keys()
   for x in [before,allchange,mixed]:assert h(x)==inputs[x.name]['sha256']
   results.append({'scenario':scenario,'mode':mode,'repeat':repeat+1,'exit':proc.returncode,'elapsed_seconds':elapsed,'peak_rss_kib_linux':usage.ru_maxrss,'report_bytes':out.stat().st_size,'counts':counts,'report_sha256':h(out)})
print(json.dumps({'synthetic_only':True,'uid':os.getuid(),'python':sys.version,'platform':platform.platform(),'inventory_hashes_verified':len(inv['files']),'cli_sha256':h(p/'csv_change.py'),'inputs':inputs,'runs':results,'input_hashes_preserved':True,'output_directory':str(work),'exact_full_positions_verified':True},indent=2),flush=True)
