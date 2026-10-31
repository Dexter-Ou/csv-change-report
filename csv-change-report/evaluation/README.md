# Try an offline export review

Audience hypothesis: someone who reviews recurring CSV exports by a stable unique
record key. This is a free, speculative evaluation kit for 0.1.8-preview, not
customer evidence or a paid offer. All supplied names and records are synthetic.
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
Use detailed CLI output separately to locate changes. Synthetic examples are
not customer evidence; independent batch-review usefulness remains unverified.

## Optional feedback

If you choose to share feedback, open an issue at
https://github.com/Dexter-Ou/csv-change-report/issues using `FEEDBACK.md` as a prompt.
An account is needed only for GitHub feedback. Public issues are public: do not
paste private exports, cell values, column names, paths, hashes, customer details
or secrets. Describe behavior in general terms or use a tiny invented example.
No feedback is sent automatically. A lack of issues does not demonstrate success.
