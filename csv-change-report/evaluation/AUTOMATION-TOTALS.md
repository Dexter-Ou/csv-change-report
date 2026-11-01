# Read partial totals from the automation caller

Run the following block once from the extracted product directory in a trusted
local workspace. Python 3.10+, no installation or network required. These are
synthetic inputs, not customer results. The exercise refuses an existing practice
directory. Keep private exports, reports and diagnostics private.

`automate-batch.py` emits a compact status object and does not save `totals.json`.
After `E_COMPARISON`, request row and column totals separately. Status 2 can carry
valid partial totals; check JSON and `partial` before using counts. Other wrapper
errors (such as `E_OUTPUT` or `E_STATUS`) need investigation, not this happy path.

```sh
python3 - <<'PYCODE'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

base = Path('caller practice')
base.mkdir()  # Refuse repeat execution; never delete an old run to reuse its name.
helpers = Path('evaluation')
def invoke(script, *args):
    result = subprocess.run([sys.executable, str(helpers / script),
                             *map(str, args)], capture_output=True, text=True)
    if result.stderr:
        raise SystemExit('Helper diagnostic: preserve files and inspect the run.')
    return result.returncode, json.loads(result.stdout)

def snapshot():
    return {str(f): hashlib.sha256(f.read_bytes()).hexdigest()
            for root in (base, Path('examples')) for f in root.rglob('*')
            if f.is_file()}

# Retain the malformed export. A repeated key needs a domain decision.
(base / 'invalid-original.csv').write_bytes(
    (helpers / 'duplicate-key.csv').read_bytes())
pair = {'before': '../examples/before.csv',
        'after': '../examples/after.csv', 'key': 'id'}
pairs = [{**pair, 'after': pair['before']}, pair,
         {**pair, 'after': 'invalid-original.csv'}]
manifest = base / 'original.json'
manifest.write_text(json.dumps({'version': 1, 'pairs': pairs}), encoding='utf-8')
failed = base / 'attempt-1'
status, result = invoke('automate-batch.py', manifest, failed)
if (status, result) != (2, {'version': 1, 'code': 'E_COMPARISON',
                           'status': 2, 'pair_count': 3}):
    raise SystemExit('Unexpected caller result; preserve this attempt.')
status, totals = invoke('batch-totals.py', failed / 'status.tsv',
                       '--expected-pairs', result['pair_count'],
                       '--row-counts', '--column-counts')
if status != 2 or totals['partial'] is not True:
    raise SystemExit('Expected partial totals; inspect the preserved run.')
print(json.dumps({'attempt': 1, 'caller': result, 'totals': totals}, sort_keys=True))

# Never treat the two successful reports as coverage of all three pairs.
# For this invented exercise ONLY, the intended third AFTER is the baseline.
# In real work resolve the cause with the data owner, then correct a separate copy.
saved = snapshot()
(base / 'corrected-copy.csv').write_bytes(Path('examples/before.csv').read_bytes())
corrected = json.loads(manifest.read_text(encoding='utf-8'))
corrected['pairs'][2]['after'] = 'corrected-copy.csv'
new_manifest = base / 'corrected.json'
with new_manifest.open('x', encoding='utf-8') as stream:
    json.dump(corrected, stream)
status, result = invoke('automate-batch.py', new_manifest, base / 'attempt-2')
if status != 1 or result['code'] != 'CHANGED':
    raise SystemExit('Unexpected retry result; preserve both attempts.')
status, totals = invoke('batch-totals.py', base / 'attempt-2/status.tsv',
                       '--expected-pairs', result['pair_count'],
                       '--row-counts', '--column-counts')
if status != 1 or totals['partial'] is not False:
    raise SystemExit('Expected complete totals; inspect both attempts.')
current = snapshot()
if any(current.get(name) != value for name, value in saved.items()):
    raise SystemExit('Earlier file changed; preserve evidence and investigate.')
print(json.dumps({'attempt': 2, 'caller': result, 'totals': totals}, sort_keys=True))
print('Earlier inputs, manifest and failed reports preserved.')
PYCODE
```

Expected first result: `E_COMPARISON`, equal=1, changed=1, error=1,
incomplete=0, partial=true. Row counts cover only successful pairs: added=1,
removed=1, changed=1, unchanged=4; column tally reports=2, changed_cells=1.
The error pair has a diagnostic and no JSON report. Inspect `attempt-1/status.tsv`
and `attempt-1/pair-0003.stderr` under `caller practice` when investigating.

Expected retry: `CHANGED`, equal=2, changed=1, error=0, partial=false,
column tally reports=3. Differences still require review; complete totals do
not approve changes. The wrapper does not repair CSVs or resume failed runs.
An occupied output gives `E_OUTPUT`; choose another fresh path. If the totals
helper emits no JSON, preserve the run and inspect its diagnostic instead of
using absent or stale counts. These observations do not test crashes, concurrent
edits or hostile paths; the walkthrough has been tested on Linux only.
