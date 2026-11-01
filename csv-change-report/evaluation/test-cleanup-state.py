from pathlib import Path
import sys,os,json,io,contextlib,importlib.util,errno,subprocess,zipfile,hashlib,tempfile
from unittest.mock import patch
if sys.platform != 'linux' or os.geteuid() == 0:
 raise SystemExit('Requires Linux and a non-root user')
p=Path(__file__).resolve().parents[1]
W=Path(tempfile.mkdtemp(prefix='csv-cleanup-state-'));b=W/'cleanup-cases';b.mkdir();checks=[]
print('Retained test files: '+str(W),file=sys.stderr)
def check(label,ok):
 checks.append({'label':label,'passed':bool(ok)})
 if not ok:raise RuntimeError(label)
v=b/'before.csv';v.write_text('id,value\n1,old\n');a=b/'after.csv';a.write_text('id,value\n1,new\n')
spec=importlib.util.spec_from_file_location('prototype',p/'csv_change.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
real_unlink=os.unlink;real_link=os.link
for label,changed,fail_link,collision in [('equal-cleanup',False,False,False),('changed-cleanup',True,False,False),('unsupported-cleanup',False,True,False),('collision-cleanup',False,False,True)]:
 d=b/label;d.mkdir();out=d/'report.json';err=io.StringIO();stdout=io.StringIO()
 def deny_unlink(path,*args,**kwargs):
  if Path(path).name.startswith('.csv-change-'):raise PermissionError(errno.EACCES,'PRIVATE SYNTHETIC ERROR MUST NOT LEAK')
  return real_unlink(path,*args,**kwargs)
 def link(src,dst):
  if fail_link:raise OSError(errno.EOPNOTSUPP,'PRIVATE SYNTHETIC ERROR MUST NOT LEAK')
  if collision:Path(dst).write_bytes(b'RACE SENTINEL')
  return real_link(src,dst)
 with patch.object(m.os,'unlink',deny_unlink),patch.object(m.os,'link',link),contextlib.redirect_stderr(err),contextlib.redirect_stdout(stdout):
  rc=m.main([str(v),str(a if changed else v),'--key','id','--check','--output',str(out)])
 messages=[json.loads(line) for line in err.getvalue().splitlines()];committed=not(fail_link or collision);temps=list(d.glob('.csv-change-*'))
 (d/'stderr.txt').write_text(err.getvalue())
 check(label+' conservative status',rc==2 and not stdout.getvalue())
 check(label+' explicit state',messages[0]['output_committed']==committed and messages[0]['cleanup_required'] is True)
 check(label+' recovery instruction', 'Do not retry the same output path' in messages[0]['recovery'])
 check(label+' no sensitive echo',all(x not in err.getvalue() for x in [str(out),str(v),'PRIVATE SYNTHETIC']))
 check(label+' leftover known',len(temps)==1)
 if committed:
  check(label+' report complete',json.loads(out.read_text())['counts']['changed']==int(changed) and out.stat().st_mode&0o777==0o600)
  check(label+' same inode',os.stat(out).st_ino==os.stat(temps[0]).st_ino)
  again=io.StringIO()
  with contextlib.redirect_stderr(again):retry=m.main([str(v),str(v),'--key','id','--output',str(out)])
  check(label+' retry refuses',retry==2 and json.loads(again.getvalue())=={'error':'output path already exists'})
 else:
  check(label+' primary error retained',len(messages)==2 and messages[1]=={'error':'output path already exists' if collision else 'output file could not be written'})
  check(label+' destination protected',out.read_bytes()==b'RACE SENTINEL' if collision else not out.exists())
 for tmp in temps:real_unlink(tmp)
 check(label+' manual cleanup preserves output',out.exists()==(committed or collision))
# Inject cleanup denial only into subprocesses of the separate batch copy.
import shutil
bp=W/'batch-injected';shutil.copytree(p,bp)
script=bp/'csv_change.py';code=script.read_text();needle="if __name__ == '__main__':\n"
assert code.count(needle)==1
code=code.replace(needle,"""if __name__ == '__main__':
    _real_unlink = os.unlink
    def _deny_cleanup(path, *args, **kwargs):
        if Path(path).name.startswith('.csv-change-'):
            raise PermissionError('synthetic cleanup denial')
        return _real_unlink(path, *args, **kwargs)
    os.unlink = _deny_cleanup
""")
script.write_text(code)
manifest=b/'batch.json';manifest.write_text(json.dumps({'version':1,'pairs':[{'before':'before.csv','after':'before.csv','key':'id'}]}));out=b/'batch-output'
r=subprocess.run([sys.executable,str(bp/'evaluation/automate-batch.py'),str(manifest),str(out)],capture_output=True,timeout=60)
(b/'batch.stdout').write_bytes(r.stdout);(b/'batch.stderr').write_bytes(r.stderr)
check('batch conservatively reports error',r.returncode==2 and json.loads(r.stdout)['code']=='E_COMPARISON')
check('batch complete output despite error',json.loads((out/'pair-0001.json').read_text())['counts']['unchanged']==1)
# Retain report/diagnostics before cleaning known test-owned temporary links.
check('batch one leftover',len(list(out.glob('.csv-change-*')))==1)
for tmp in out.glob('.csv-change-*'):real_unlink(tmp)
check('inputs preserved',v.read_text()=='id,value\n1,old\n' and a.read_text()=='id,value\n1,new\n')
result={'synthetic':True,'uid':os.geteuid(),'checks':checks,'all_passed':all(x['passed'] for x in checks),'limits':['Injected Linux filesystem behavior only','Batch treats complete-but-cleanup-failed report as error','No cross-platform/crash/race guarantee'],'candidate_sha256':hashlib.sha256((p/'csv_change.py').read_bytes()).hexdigest()}
(W/'cleanup-results.json').write_text(json.dumps(result,indent=2))
with zipfile.ZipFile(W/'cleanup-samples.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in b.rglob('*'):
  if n.is_file():z.write(n,n.relative_to(W))
print(json.dumps({'results_path':str(W),'result':result}))
