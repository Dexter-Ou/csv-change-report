# Recover from a damaged retained report

Run this block once from the extracted product directory in a trusted local
workspace. Python 3.10+, no installation or network required. All inputs are
synthetic. This deliberately truncates a separate report copy after its writer
has exited; it does not simulate a process crash or repair damaged JSON.
Keep private inputs, reports and diagnostics private.

A status table records comparison outcomes. Default status-only totals do not
open reports, so a changed status can survive report damage. Requesting row or
column totals validates the reports and refuses damaged data without JSON totals.
Do not use old totals when that validation fails.

```sh
python3 - <<'PYCODE'
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

base = Path('damaged report practice')
base.mkdir()  # Refuse repeat execution; preserve existing practice runs.
helpers = Path('evaluation')
def run(script, *args):
    return subprocess.run([sys.executable, str(helpers / script),
                           *map(str, args)], capture_output=True, text=True)
def snapshot(root):
    return {str(f): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in root.rglob('*') if f.is_file()}

# Keep exact inputs and their relative references for regeneration.
for name in ('before.csv', 'after.csv'):
    shutil.copyfile(Path('examples') / name, base / name)
manifest = base / 'original.json'
with manifest.open('x', encoding='utf-8') as stream:
    json.dump({'version': 1, 'pairs': [
        {'before': 'before.csv', 'after': 'after.csv', 'key': 'id'}]}, stream)
original = base / 'original-run'
result = run('automate-batch.py', manifest, original)
if result.returncode != 1 or json.loads(result.stdout)['code'] != 'CHANGED':
    raise SystemExit('Unexpected baseline; preserve the run and inspect diagnostics.')
original_hashes = snapshot(base)

# Artificial damage is confined to a separate practice copy.
damaged = base / 'damaged-copy'
shutil.copytree(original, damaged)
report = damaged / 'pair-0001.json'
raw = report.read_bytes()
report.write_bytes(raw[:len(raw) // 2])
saved = snapshot(base)
status = run('batch-totals.py', damaged / 'status.tsv', '--expected-pairs', 1)
expected = dict(expected=1, completed=1, equal=0, changed=1, error=0, incomplete=0)
if status.returncode != 1 or json.loads(status.stdout) != expected:
    raise SystemExit('Unexpected recorded statuses; preserve evidence.')
print(json.dumps({'recorded_status_only': expected}, sort_keys=True))

validated = run('batch-totals.py', damaged / 'status.tsv', '--expected-pairs', 1,
                '--row-counts', '--column-counts')
if (validated.returncode != 2 or validated.stdout or
        not validated.stderr.startswith('Cannot summarize:')):
    raise SystemExit('Unexpected damaged-report validation; preserve evidence.')
print('Damaged report: status 2, no JSON totals. Preserve its diagnostic:')
print(validated.stderr, end='')

# Recompute from retained inputs; never patch the report or reuse its directory.
fresh = base / 'regenerated-run'
retry = run('automate-batch.py', manifest, fresh)
if retry.returncode != 1 or json.loads(retry.stdout)['code'] != 'CHANGED':
    raise SystemExit('Unexpected regeneration; preserve all runs.')
totals = run('batch-totals.py', fresh / 'status.tsv', '--expected-pairs', 1,
             '--row-counts', '--column-counts')
if totals.returncode != 1 or json.loads(totals.stdout)['partial'] is not False:
    raise SystemExit('Regenerated totals unavailable; inspect diagnostics.')
current = snapshot(base)
if any(current.get(n) != v for n, v in saved.items()):
    raise SystemExit('Earlier file changed; preserve evidence and investigate.')
if any(current.get(n) != v for n, v in original_hashes.items()):
    raise SystemExit('Original input or baseline changed; investigate.')
print(json.dumps({'regenerated_totals': json.loads(totals.stdout)}, sort_keys=True))
print('Retained inputs, manifest, original run and damaged copy unchanged.')
PYCODE
```

Expected recorded statuses: completed=1, changed=1, error=0, incomplete=0.
These do not certify report integrity. The damaged copy then refuses row/column
totals with status 2 and no JSON output. Regeneration returns status 1 with
partial=false, rows added=1, removed=1, changed=1, unchanged=1; column tally
reports=1 and changed_cells=1. Status 1 still requires review of differences.

For real work, first stop writers and preserve damaged files and diagnostics.
Recover the exact retained inputs and manifest from trusted copies; if unavailable,
stop and resolve that gap rather than inventing replacement data. A fresh run
recomputes comparisons; it does not prove that retained CSVs match lost originals.
Hashes here check ordinary files at observation time, not atomicity or protection
against hostile concurrent edits. Linux tested only; no crash-durability claim.
