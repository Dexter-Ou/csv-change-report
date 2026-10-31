# Worked example: partial totals from a mixed batch

Run from the folder containing csv_change.py, using Python 3.10+ and a POSIX
shell. No installation or network is needed. All records are invented. Use a
trusted directory: the commands create `mixed demo` and stop if it exists.
Preserve the outputs; choose a fresh extraction or unused directory to reset.

The first pair adds a row, the second removes a row, the third is equal, and
the fourth deliberately uses a missing key. Copy this entire block, including
the exit-status checks. It works when the calling shell uses `set -e`.

```sh
(
set -eu
mkdir 'mixed demo'
printf 'id,status\nA,open\n' > 'mixed demo/one.csv'
printf 'id,status\nA,open\nB,closed\n' > 'mixed demo/two.csv'
printf 'id,status\n' > 'mixed demo/empty.csv'
batch_status=0
sh evaluation/batch-review.sh --totals 'mixed demo/reports' \
  'mixed demo/one.csv' 'mixed demo/two.csv' id \
  'mixed demo/one.csv' 'mixed demo/empty.csv' id \
  'mixed demo/one.csv' 'mixed demo/one.csv' id \
  'mixed demo/one.csv' 'mixed demo/two.csv' missing_key || batch_status=$?
printf 'batch exit: %s\n' "$batch_status"
test "$batch_status" -eq 2
cat 'mixed demo/reports/status.tsv'
totals_status=0
python3 evaluation/batch-totals.py 'mixed demo/reports/status.tsv' \
  --expected-pairs 4 --row-counts --column-counts \
  > 'mixed demo/totals.json' || totals_status=$?
printf 'totals exit: %s\n' "$totals_status"
test "$totals_status" -eq 2
python3 - <<'PYTHON'
import json
from pathlib import Path
report = json.loads(Path('mixed demo/totals.json').read_text())
for field in ('equal', 'changed', 'error', 'partial', 'rows', 'column_tally'):
    print(field + ':', json.dumps(report[field], sort_keys=True))
PYTHON
)
```

Expected printed counts (the status table and exit messages also appear):

```text
equal: 1
changed: 2
error: 1
partial: true
rows: {"added": 1, "changed": 0, "removed": 1, "unchanged": 2}
column_tally: {"changed_cells": 0, "changed_records": 0, "columns": [{"changed_cells": 0, "column": "status"}], "reports": 3}
```

The status table has pair statuses `1`, `1`, `0`, `2` in order. Both commands
exit 2 because the fourth comparison failed. The subshell finishes successfully
only after checking those expected error statuses and printing the counts; this
is an example check, not permission to ignore exit 2 in production automation.
Inspect `mixed demo/reports/pair-0004.stderr` for the missing-key diagnostic.

The row totals include only the three successful reports. Unchanged counts sum
across pairs: row A is unchanged once in the added-row pair and once in the equal
pair. Added/removed rows do not count as changed records or changed cells in the
column tally. A zero column tally therefore does not mean the batch is equal.
The failed pair contributes no row or column counts; `partial: true` means these
are incomplete batch totals. Do not present them as totals for all four pairs.

`--totals` also saves row totals in `mixed demo/reports/totals.json`; the second
command reads the status table and reports to add a column tally without changing
them. Fix the key and rerun into a new report directory for complete totals.
Reports omit cell values but expose filenames, column names and counts. These
Linux-checked commands do not establish Windows/macOS behavior. See
[RECOVERY.md](RECOVERY.md) for interrupted batches and trusted-directory limits.


## Correct the key and keep the partial batch

After the first block, copy this entire continuation. It uses the same CSVs,
changes only the fourth key to `id`, and writes to a new report directory.
The original partial reports and totals are retained. The snapshot check below
compares their file contents before and after the rerun; use a trusted directory.
It is a content check, not protection against concurrent filesystem changes.

```sh
(
set -eu
python3 - <<'PYTHON'
import hashlib, json
from pathlib import Path
paths = sorted(Path('mixed demo/reports').rglob('*'))
paths.append(Path('mixed demo/totals.json'))
hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in paths if p.is_file()}
with Path('mixed demo/partial-hashes.json').open('x') as target:
    json.dump(hashes, target, sort_keys=True)
PYTHON
batch_status=0
sh evaluation/batch-review.sh --totals 'mixed demo/corrected reports' \
  'mixed demo/one.csv' 'mixed demo/two.csv' id \
  'mixed demo/one.csv' 'mixed demo/empty.csv' id \
  'mixed demo/one.csv' 'mixed demo/one.csv' id \
  'mixed demo/one.csv' 'mixed demo/two.csv' id || batch_status=$?
printf 'corrected batch exit: %s\n' "$batch_status"
test "$batch_status" -eq 1
cat 'mixed demo/corrected reports/status.tsv'
totals_status=0
python3 evaluation/batch-totals.py 'mixed demo/corrected reports/status.tsv' \
  --expected-pairs 4 --row-counts --column-counts \
  > 'mixed demo/corrected totals.json' || totals_status=$?
printf 'corrected totals exit: %s\n' "$totals_status"
test "$totals_status" -eq 1
python3 - <<'PYTHON'
import hashlib, json
from pathlib import Path
expected = json.loads(Path('mixed demo/partial-hashes.json').read_text())
paths = sorted(Path('mixed demo/reports').rglob('*'))
paths.append(Path('mixed demo/totals.json'))
actual = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in paths if p.is_file()}
if actual != expected:
    raise SystemExit('Original partial outputs changed')
print('original partial outputs: unchanged')
report = json.loads(Path('mixed demo/corrected totals.json').read_text())
for field in ('equal', 'changed', 'error', 'partial', 'rows', 'column_tally'):
    print(field + ':', json.dumps(report[field], sort_keys=True))
PYTHON
)
```

Expected printed counts for this continuation:

```text
original partial outputs: unchanged
equal: 1
changed: 3
error: 0
partial: false
rows: {"added": 2, "changed": 0, "removed": 1, "unchanged": 3}
column_tally: {"changed_cells": 0, "changed_records": 0, "columns": [{"changed_cells": 0, "column": "status"}], "reports": 4}
```

Corrected pair statuses are `1`, `1`, `0`, `1`. Both commands exit 1 because
there are differences and no comparison errors. Exit 1 here does not mean the
commands failed to produce reports. The fourth successful pair now contributes
one added and one unchanged row, so these totals cover all four pairs.

Do not reuse `mixed demo/corrected reports` for another batch. Preserve both
report directories to compare the partial and complete outcomes. This continuation
also refuses to replace its existing snapshot file on a repeat run. Choose a
fresh extraction to repeat both examples from the start.
