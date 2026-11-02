"""Run synthetic CSV comparisons against bundled or explicitly selected source; Python 3.10+, standard library."""
from pathlib import Path
import argparse,contextlib,base64,binascii,hashlib,io,json,subprocess,sys,tempfile,zipfile
R=Path(__file__).resolve().parent
SOURCE_COMMIT="6dffce2b04e7e5b88100287611773e500ae0e6d9"
PACKAGE_SHA256="52b84c9420eed39fa7df1d7c13b89cd64279e2f1b67a31fa75185f8a9a91a6d4"
cases=[('Detailed text',['examples/before.csv','examples/after.csv','--key','id','--format','text'],0),('Detailed JSON',['examples/before.csv','examples/after.csv','--key','id'],0),('Summary JSON',['examples/before.csv','examples/after.csv','--key','id','--summary-only'],0),('Changed check',['examples/before.csv','examples/after.csv','--key','id','--check','--summary-only'],1),('Equal check',['examples/before.csv','examples/before.csv','--key','id','--check','--summary-only'],0),('Invalid duplicate key',['examples/before.csv','evaluation/duplicate-key.csv','--key','id','--check'],2)]
@contextlib.contextmanager
def select_product(source):
    if source is not None:
        product=source.expanduser().resolve()
        required=['csv_change.py','examples/before.csv','examples/after.csv','evaluation/duplicate-key.csv']
        if not all((product/name).is_file() for name in required):
            raise ValueError('--source must name the product directory containing csv_change.py and synthetic fixtures')
        print('Source mode: explicit checkout')
        print('Comparator SHA-256: '+hashlib.sha256((product/'csv_change.py').read_bytes()).hexdigest())
        yield product
        return
    packages=sorted(R.glob('package.zip.b64.part*'))
    try:
        raw=base64.b64decode(b''.join(p.read_bytes() for p in packages).strip(),validate=True)
    except (OSError,binascii.Error):
        raw=b''
    if hashlib.sha256(raw).hexdigest()!=PACKAGE_SHA256:
        raise ValueError('Bundled package missing or hash mismatch')
    with tempfile.TemporaryDirectory(prefix='csv-terminal-tour-') as temp:
        destination=Path(temp)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for name in archive.namelist():
                if Path(name).is_absolute() or '..' in Path(name).parts:
                    raise ValueError('Unsafe archive member')
            archive.extractall(destination)
        product=next(destination.iterdir())/'csv-change-report'
        print('Source mode: bundled historical snapshot '+SOURCE_COMMIT)
        print('Comparator SHA-256: '+hashlib.sha256((product/'csv_change.py').read_bytes()).hexdigest())
        yield product

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,help='Trusted product directory containing csv_change.py; executes that code on synthetic fixtures')
    options=parser.parse_args()
    if sys.flags.optimize:
        print('Run without -O so verification assertions remain enabled.',file=sys.stderr)
        return 2
    with select_product(options.source) as product:
        for title,args,status in cases:
            result=subprocess.run([sys.executable,'csv_change.py']+args,cwd=product,capture_output=True,text=True,timeout=20)
            if result.returncode!=status:
                raise AssertionError(f'{title}: expected {status}, got {result.returncode}')
            if title in ['Detailed JSON','Summary JSON','Changed check']:
                assert json.loads(result.stdout)['counts']==dict(before=3,after=3,added=1,removed=1,changed=1,unchanged=1)
            if title=='Equal check':
                assert json.loads(result.stdout)['counts']['unchanged']==3
            if title=='Invalid duplicate key':
                assert not result.stdout and 'repeats a key' in json.loads(result.stderr)['error']
            for value in ['alpha@example.test','beta@example.test']:
                assert value not in result.stdout
            print('## '+title)
            print('$ python3 csv_change.py '+' '.join(args))
            print(result.stdout.rstrip() or '(stdout empty)')
            print('stderr: '+result.stderr.rstrip() if result.stderr else '(stderr empty)')
            print('exit status: '+str(result.returncode))
        print('PASS: six synthetic examples; expected statuses, counts and privacy checks.')
    return 0
if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError,ValueError,zipfile.BadZipFile) as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(2)
