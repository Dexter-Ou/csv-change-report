# Preserve a stopped batch and retry safely offline

Run these blocks in order from the extracted product directory, in a trusted
local directory, once. Requires Python 3 and a POSIX shell; no network or installs.
All data here are synthetic. This exercise simulates a stopped table; it does
not test killing a process, power loss, or crash durability. Never edit an actual
stopped run to make it look complete. First ensure its writer has stopped.

## 1. Keep the inputs and original attempt

Create a new exercise directory; an existing directory must make this block fail.
Save the exact order of BEFORE/AFTER/KEY triples locally for real work. Reports
contain hashes and column names; keep private exports and diagnostics private.

```sh
mkdir './recovery practice' || exit 2
cp evaluation/duplicate-key.csv './recovery practice/invalid-original.csv'
status=0
sh evaluation/batch-review.sh './recovery practice/attempt-1' \
  examples/before.csv examples/before.csv id \
  examples/before.csv examples/after.csv id \
  examples/before.csv './recovery practice/invalid-original.csv' id || status=$?
printf 'Original attempt status: %s\n' "$status"
[ "$status" -eq 2 ] || exit 2
cat './recovery practice/attempt-1/pair-0003.stderr'
```

This actual completed batch has equal, changed, error statuses 0, 1, 2. The third
pair repeats a key. Keep the invalid input and diagnostics; a repeated key needs
a domain decision, not automatic deduplication.

## 2. Practice recognizing missing work

Create a **simulated** stopped snapshot containing only the first completed row
and its files. The original attempt stays intact. For a real stopped batch, skip
this simulation and inspect the untouched stopped directory instead.

```sh
python3 - <<'PY'
from pathlib import Path
import shutil
base = Path('recovery practice')
source = base / 'attempt-1'
target = base / 'simulated-stopped'
target.mkdir()
lines = (source / 'status.tsv').read_bytes().splitlines(keepends=True)
(target / 'status.tsv').write_bytes(b''.join(lines[:2]))
for suffix in ('json', 'stdout', 'stderr'):
    shutil.copyfile(source / ('pair-0001.' + suffix), target / ('pair-0001.' + suffix))
PY
status=0
python3 evaluation/batch-totals.py './recovery practice/simulated-stopped/status.tsv' \
  --expected-pairs 3 || status=$?
printf 'Stopped snapshot totals status: %s\n' "$status"
[ "$status" -eq 2 ] || exit 2
```

Expected: completed=1, equal=1, changed=0, error=0, incomplete=2. Status 2 does
not explain why work is missing. A truncated last row may instead reject the
whole table. Retain every report and diagnostic, even ones absent from the table.
The helper cannot resume a run or verify its report contents. A wrong expected
pair count can hide missing work; use the original command, not row count.

## 3. Correct a copy, then run every pair into a new directory

For this invented exercise only, the intended third AFTER is the unchanged
baseline. Copy that known fixture to a new filename. This is an explicit practice
replacement, not a rule for fixing real duplicate records. For real work, retain
the original, resolve the cause with the data owner, and correct a separate copy.
No prior report directory or original input is overwritten.

```sh
cp examples/before.csv './recovery practice/corrected-copy.csv'
status=0
sh evaluation/batch-review.sh './recovery practice/attempt-2' \
  examples/before.csv examples/before.csv id \
  examples/before.csv examples/after.csv id \
  examples/before.csv './recovery practice/corrected-copy.csv' id || status=$?
printf 'New attempt status: %s\n' "$status"
[ "$status" -eq 1 ] || exit 2
status=0
python3 evaluation/batch-totals.py './recovery practice/attempt-2/status.tsv' \
  --expected-pairs 3 || status=$?
printf 'New attempt totals status: %s\n' "$status"
[ "$status" -eq 1 ] || exit 2
cat './recovery practice/attempt-2/status.tsv'
```

Expected: completed=3, equal=2, changed=1, error=0, incomplete=0. Pair-0002 still
needs change review; a successful retry is not approval. Both previous snapshots
remain useful evidence. Reusing attempt-1 or attempt-2 is refused; choose a new
unused directory for every later attempt. Do not delete a failed run to reuse its
name. Windows/macOS, concurrent writers and crash recovery remain untested.

## 4. Separate manifest preflight from CSV execution

This separate synthetic exercise uses a schema-valid manifest whose second AFTER
file is missing. Run from the product directory in the same trusted workspace.
Preflight checks the manifest, not whether its CSVs exist or can be compared.

```sh
mkdir './manifest recovery' || exit 2
python3 - <<'PY'
import json
from pathlib import Path
base = Path('manifest recovery')
pairs = [
    {'before': '../examples/before.csv', 'after': '../examples/after.csv', 'key': 'id'},
    {'before': '../examples/before.csv', 'after': 'missing.csv', 'key': 'id'},
    {'before': '../examples/before.csv', 'after': '../examples/before.csv', 'key': 'id'},
]
(base / 'original.json').write_text(json.dumps({'version': 1, 'pairs': pairs}), encoding='utf-8')
PY
python3 evaluation/batch-manifest.py --validate-only \
  './manifest recovery/original.json' './manifest recovery/preflight-reports'
[ ! -e './manifest recovery/preflight-reports' ] || exit 2
[ ! -e './manifest recovery/missing.csv' ] || exit 2
```

Expected preflight status: 0, with `Manifest valid: 3 pair(s); CSV files not checked; no reports created.`
No report directory is created. The missing CSV remains missing.

```sh
status=0
python3 evaluation/batch-manifest.py --totals \
  './manifest recovery/original.json' './manifest recovery/attempt-1' || status=$?
printf 'Manifest execution status: %s\n' "$status"
[ "$status" -eq 2 ] || exit 2
cat './manifest recovery/attempt-1/status.tsv'
cat './manifest recovery/attempt-1/pair-0002.stderr'
cat './manifest recovery/attempt-1/totals.json'
[ ! -e './manifest recovery/attempt-1/pair-0002.json' ] || exit 2
```

Expected pair statuses: 1, 2, 0. The missing file produces an error with report
`-`; the final pair still runs. Totals are partial: completed=3, changed=1,
error=1, equal=1, incomplete=0. Row totals cover only successful comparisons;
they are not totals for the whole intended batch. Keep the original manifest,
status table, reports and diagnostics together. Diagnostics may contain paths.

## 5. Correct a separate manifest and preserve the failed run

For this exercise only, the intended second AFTER is the unchanged baseline.
Create a corrected manifest under a new name, pointing to that known fixture.
For real data, resolve the missing export with its owner; do not substitute an
unrelated CSV just to obtain a successful status. Preflight does not pin inputs.

```sh
python3 - <<'PY'
import json
from pathlib import Path
base = Path('manifest recovery')
data = json.loads((base / 'original.json').read_text(encoding='utf-8'))
data['pairs'][1]['after'] = '../examples/before.csv'
with (base / 'corrected.json').open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(data))
PY
python3 evaluation/batch-manifest.py --validate-only './manifest recovery/corrected.json'
status=0
python3 evaluation/batch-manifest.py --totals \
  './manifest recovery/corrected.json' './manifest recovery/attempt-2' || status=$?
printf 'Corrected manifest execution status: %s\n' "$status"
[ "$status" -eq 1 ] || exit 2
cat './manifest recovery/attempt-2/status.tsv'
cat './manifest recovery/attempt-2/totals.json'
```

Expected pair statuses: 1, 0, 0, with complete totals: completed=3, changed=1,
equal=2, error=0, incomplete=0. Changed records still need review. Attempt-1 and
original.json remain unchanged; the corrected manifest does not repair old reports.
Choose a new unused report directory for each execution. This walkthrough tests
synthetic files on Linux, not crash recovery or concurrent edits.
