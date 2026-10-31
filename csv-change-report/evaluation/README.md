# Try an offline export review

Review recurring CSV exports by a stable unique record key. This free evaluation
kit accompanies 0.1.10-preview. All supplied names and records are synthetic.
Python 3.10+ and a POSIX shell are required; no install, network or account needed
to run. Windows shell behavior has not been tested.

## Task (about five minutes; an estimate, not measured user timing)

Imagine approving a new export for a local workflow. Before using it, determine
whether records were added, removed or changed. Keep both snapshots intact.
From the extracted `csv-change-report` directory:

```sh
sh evaluation/review.sh examples/before.csv examples/after.csv id
sh evaluation/review.sh examples/before.csv examples/before.csv id
sh evaluation/review.sh examples/before.csv evaluation/duplicate-key.csv id
```

The first two commands should exit 0 because a comparison completed; the wrapper
handles the raw CLI's change status 1 explicitly. The third should exit 2, with a
fixed JSON diagnostic on stderr and a failure message. Do not add `set -e` around
the raw CLI without handling its expected status 1. See `EXPECTED.md` for the
answer key. Reports do not contain old/new cell values: inspect your original
snapshots locally to decide whether a change is acceptable.

For your own files, use copies in a trusted local directory, quote the paths and
provide the exact case-sensitive unique key column name:

```sh
sh evaluation/review.sh '/path/to/before.csv' '/path/to/after.csv' 'record_id'
```

The wrapper prints a text report to the terminal. Do not redirect onto an input.
It does not modify files or save reports. If it fails, preserve originals, fix a
copy of invalid input, or check Python/version/path/key, then rerun. Duplicate
keys need a domain decision; never silently discard records to make a test pass.
The main README describes input limits, exact comparisons and exclusive
`--output` behavior. For automation that needs 0=equal, 1=changed, 2=error, use
`csv_change.py --check` directly; this demonstration wrapper consumes 1.

## Try explicit volatile-column exclusions

These original synthetic exports add an `exported_at` timestamp. Run the raw
CLI from the extracted product directory. Each command prints a JSON report;
`--check` uses 0=equal under this comparison, 1=changed, 2=error. These commands
explicitly handle all three statuses and can also run in a `set -e` shell:

```sh
status=0
python3 csv_change.py evaluation/volatile-before.csv evaluation/volatile-only.csv --key id --check || status=$?
printf 'CLI status: %s\n' "$status"

status=0
python3 csv_change.py evaluation/volatile-before.csv evaluation/volatile-only.csv --key id --check --ignore-column exported_at || status=$?
printf 'CLI status: %s\n' "$status"

status=0
python3 csv_change.py evaluation/volatile-before.csv evaluation/retained-change.csv --key id --check --ignore-column exported_at || status=$?
printf 'CLI status: %s\n' "$status"
```

Expected statuses are 1, 0, 1. See `EXPECTED.md` for counts and positions.
Only exclude a field when your workflow deliberately permits ignoring it.
With exclusions, status 0 means equality of retained fields and keyed membership,
not full export equality. Full input hashes still differ. Exclusions do not
suppress schema/format errors or added/removed records. Names are exact and
case-sensitive; key columns and absent columns cannot be excluded. Repeat
`--ignore-column NAME` for multiple fields. `review.sh` intentionally accepts
only BEFORE, AFTER and KEY: use the raw CLI for exclusions.

## Compare summary and detailed reports

Use the same synthetic export pair to decide whether a compact overview is
sufficient or you need record positions. Run from the extracted product folder.
Each command safely captures the expected change status, including in a shell
using `set -e`. These commands print reports; they do not save or modify files.

```sh
status=0
python3 csv_change.py examples/before.csv examples/after.csv --key id --summary-only --check || status=$?
printf 'Summary CLI status: %s\n' "$status"

status=0
python3 csv_change.py examples/before.csv examples/after.csv --key id --check || status=$?
printf 'Detailed CLI status: %s\n' "$status"
```

Both statuses should be 1. Compare counts, full-input hashes and column totals;
they should match. Which report identifies the changed record's position?
Can the summary identify which added record needs review? Check `EXPECTED.md`.
For a human-readable overview, add `--format text` to the summary command.
Summary mode omits record positions and per-record changes. Neither mode prints
cell values; use the original snapshots locally for that decision. Summary mode
still reads both full snapshots into memory; smaller output is not a streaming
or performance claim. It is not a privacy guarantee: hashes and column names
remain in JSON. Use default detailed output when you need locations.

To check equal/error handling, repeat the summary command using
`examples/before.csv` as AFTER (expected status 0), then
`evaluation/duplicate-key.csv` as AFTER (expected status 2, stderr diagnostic,
empty stdout). Never interpret status 2 as an unchanged export. These are
synthetic practice tasks; review speed and usefulness remain unmeasured.

## Review several pairs offline

Run from the extracted product folder in a trusted local directory. The helper
accepts a new report directory followed by BEFORE, AFTER, KEY triples. Quote
paths and key names. No manifest is evaluated as shell code. Numeric names follow
argument order, so repeated basenames and spaces cannot collide. It runs every
pair even when one comparison fails; it does not approve exports automatically.

```sh
status=0
sh evaluation/batch-review.sh './batch reports' \
  examples/before.csv examples/before.csv id \
  examples/before.csv examples/after.csv id \
  examples/before.csv evaluation/duplicate-key.csv id || status=$?
printf 'Batch status: %s\n' "$status"
cat './batch reports/status.tsv'
```

Expected batch status: 2. The tab-separated status table records pair-0001,
pair-0002, pair-0003 with raw CLI statuses 0, 1, 2 respectively. The first two
have summary JSON reports; the invalid pair has report `-` and its fixed
diagnostic in `pair-0003.stderr`. Each pair also has a `.stdout` capture (normally
empty). Pair order is the only mapping to the supplied paths; retain your command
locally if needed. The table contains no input paths or key names.

Batch exit status is 2 if any pair errors (including unexpected CLI statuses),
otherwise 1 if any pair changed, otherwise 0. Inspect each raw status: an error
is never equality. A missing Python interpreter may produce raw status 127.
An interruption or disk/write failure can leave an incomplete directory/table;
there is no resume, transaction or crash-durability guarantee. Treat incomplete
runs as failures, preserve diagnostics and rerun into a different new directory.
Existing report directories are refused, never reused. Parent directory must
exist. No input file is edited. Avoid untrusted/shared writable directories;
this helper does not defend against another process altering its files.
Reports retain hashes and column names, and summary reports omit positions.
Use detailed CLI output separately to locate changes. Examples use synthetic data.

## Interpret a mixed batch and choose a detailed review

Use the three-pair command above once in a fresh directory. Before consulting
`EXPECTED.md`, answer: does batch status 2 mean all three comparisons failed?
Which pair needs a data correction, and which successful pair needs change review?
The numeric pair names map to the order of triples in your command, not filenames.

Inspect the changed pair's summary and the invalid pair's diagnostic:

```sh
cat './batch reports/pair-0002.json'
cat './batch reports/pair-0003.stderr'
```

Now locate changes in pair-0002 with a separate detailed report. Reuse its exact
BEFORE, AFTER and KEY triple from your original command; do not infer paths from
the table or run table contents as commands. Run this block once; it refuses an
existing detailed output rather than overwriting it:

```sh
status=0
python3 csv_change.py examples/before.csv examples/after.csv --key id --check \
  --output './batch reports/pair-0002-detail.json' || status=$?
printf 'Detailed pair-0002 status: %s\n' "$status"
if [ "$status" -ne 1 ]; then
  printf 'Expected a completed changed comparison; inspect the diagnostic.\n' >&2
  exit 2
fi
cat './batch reports/pair-0002-detail.json'
```

Compare summary and detail counts and hashes, then find the changed column and
record positions. Use original snapshots locally to judge the values. Pair-0001
needs no content-change review under this keyed comparison; pair-0003 still needs
a domain decision about repeated keys. Reviewing pair-0002 does not repair that
error or approve the batch. Preserve the partial/error evidence; after correcting
a copy of invalid input, use a different new report directory. See the answer key
for exact expected results. This exercise tests mechanics, not human review speed.

## Count batch results, including missing pairs

Run after the batch process has stopped. Supply the number of BEFORE/AFTER/KEY
triples in your original command; the table alone cannot reveal missing trailing
pairs. For the three-pair mixed example above:

```sh
status=0
python3 evaluation/batch-totals.py './batch reports/status.tsv' --expected-pairs 3 || status=$?
printf 'Totals status: %s\n' "$status"
```

Expected JSON counts: expected=3, completed=3, equal=1, changed=1, error=1,
incomplete=0; status 2. A header plus only the first equal row, with expected=3,
gives completed=1, equal=1, incomplete=2 and status 2. Header-only means every
expected pair is incomplete. Status 0 means every expected row says equal;
1 means completed rows include changes with no errors or missing pairs; 2 means
an error, incomplete run or invalid table. Malformed tables emit a fixed diagnostic
and no totals. Unexpected numeric CLI statuses count as errors. Duplicate,
out-of-order, excess, truncated and inconsistent rows are rejected.

This reads only the status table; it does not verify report bytes, diagnose why
pairs are missing, or certify export approval. An incorrect expected count or
edited table can mislead. Preserve the original command and diagnostics. Do not
summarize a running batch; no concurrent-write/crash guarantee is provided.
The helper writes only stdout/stderr and never modifies the table or reports.

## Practice preserving a stopped run

Follow [the offline recovery exercise](RECOVERY.md) to inspect missing work,
retain invalid originals, correct a separate synthetic input copy and rerun all
pairs into a new directory. It explicitly simulates a stopped table; it does not
test process interruption or crash durability.

## Optional feedback

If you choose to share feedback, open an issue at
https://github.com/Dexter-Ou/csv-change-report/issues using `FEEDBACK.md` as a prompt.
An account is needed only for GitHub feedback. Public issues are public: do not
paste private exports, cell values, column names, paths, hashes, customer details
or secrets. Describe behavior in general terms or use a tiny invented example.
No feedback is sent automatically. A lack of issues does not demonstrate success.

### Optional batch input budget

For a tighter raw-byte limit on each before/after input, place the option first:

```sh
sh evaluation/batch-review.sh --max-input-bytes 4096 './budget reports' \
  examples/before.csv examples/after.csv id
```

Omitting the option retains the 10 MiB limit. N must be a canonical positive
base-10 integer from 1 through 10485760 (no leading zeros). Invalid options fail
before creating a directory. An over-budget pair records status 2 and no JSON
report; later pairs still run. Batch status 2 overrides changed status 1.
The limit bounds raw bytes per input, not total memory. Preserve a failed batch
and retry reviewed inputs in a fresh directory; see RECOVERY.md.

## Optional six-task reader worksheet

Start at [READER-START.md](READER-START.md). Record your answers to
[READER-TASK.md](READER-TASK.md) before consulting [ANSWER-KEY.md](ANSWER-KEY.md).
These tasks use bundled synthetic inputs; no independent reader results exist.

### Optional batch ignored column

Use one exact column name for every pair in a batch. Options precede the new
report directory; the two options may appear in either order. Use `--` to end
options if the directory name matches an option. Missing, empty or repeated
option values fail with status 2 before creating a report directory.

```sh
status=0
sh evaluation/batch-review.sh --ignore-column exported_at --max-input-bytes 4096 './timestamp batch' \
  evaluation/volatile-before.csv evaluation/volatile-only.csv id \
  evaluation/volatile-before.csv evaluation/retained-change.csv id || status=$?
printf 'Batch status: %s\n' "$status"
cat './timestamp batch/status.tsv'
```

Expected batch status: 1; pair-0001 status 0 (only timestamps changed),
pair-0002 status 1 (a meaningful status change remains). Ignoring an unknown
column or the key is a per-pair error (2); later pairs still run. Additions and
removals still count. Byte limits still apply to the complete raw input,
including ignored fields. This helper supports a single ignored column, while
the underlying CLI supports repeated `--ignore-column` arguments. Choose an
unused output directory; existing reports are preserved. Examples use synthetic data.

### Quote a column name containing spaces

POSIX shells split unquoted spaces into separate arguments. Single-quote the
entire exact name: `--ignore-column 'exported at'`. This invented example creates
a fresh private working directory and two small CSV copies; run it from the
extracted product directory. Choose an unused directory name before rerunning.

```sh
(umask 077; mkdir './quoted-column-demo') || exit 2
printf 'id,exported at,status\n1,old,open\n' > './quoted-column-demo/before.csv'
printf 'id,exported at,status\n1,new,open\n' > './quoted-column-demo/after.csv'
status=0
sh evaluation/batch-review.sh --ignore-column 'exported at' './quoted-column-demo/reports' \
  './quoted-column-demo/before.csv' './quoted-column-demo/after.csv' id || status=$?
printf 'Quoted batch status: %s\n' "$status"
cat './quoted-column-demo/reports/status.tsv'
```

Expected batch status: 0 and pair-0001 status 0: only the deliberately excluded
field changed. This means retained-field equality, not full-file equality.
Changing `status` would still count. Names remain case-sensitive, including
spaces; quoting preserves the name rather than changing matching rules.


### Optional aggregate row counts

Add `--totals` before the report directory to write `totals.json` beside
`status.tsv`, without a separate helper command:

```sh
status=0
sh evaluation/batch-review.sh --totals './aggregate reports' \
  examples/before.csv examples/after.csv id || status=$?
printf 'Batch status: %s\n' "$status"
cat './aggregate reports/totals.json'
```

The JSON retains pair totals (`equal`, `changed`, `error`, `incomplete`,
`expected`, `completed`) and adds `rows` with summed `added`, `removed`,
`changed` and `unchanged` counts. These are sums across successful pairs,
not deduplicated records across files. Failed pairs contribute no row counts;
`partial: true` means the totals exclude failed or incomplete pairs. An all-error
batch therefore has zero included rows, not evidence that its inputs were empty.
Exit statuses remain 0 for all equal, 1 for differences, and 2 for any error.
`totals.stderr` records aggregation diagnostics. An unreadable or malformed report
produces no `totals.json` and status 2; keep the pair reports for inspection.
Options can be combined with `--ignore-column` and `--max-input-bytes`.
Without `--totals`, no aggregate files are created. Repeated `--totals` fails
before creating the report directory. The underlying CSV CLI is unchanged.

For a preserved batch, the equivalent manual command is
`python3 evaluation/batch-totals.py REPORT_DIR/status.tsv --expected-pairs N --row-counts`.
Only use row aggregation on a trusted batch directory you generated; do not let
another process edit its reports while summarizing. Tests used synthetic inputs on Linux.
