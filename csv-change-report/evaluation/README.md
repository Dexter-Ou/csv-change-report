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
synthetic practice tasks.

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
otherwise 1 if any pair changed, otherwise 0. Inspect each pair status: an error
is never equality. Unexpected comparator statuses (including a missing interpreter)
are normalized to 2. Before recording 0 or 1, the helper validates a regular,
nonempty version 2 summary: JSON fields, counts, hashes, column totals and
agreement with the comparator status. Invalid reports are retained for inspection
but have report `-` in the table. Validation checks structure and internal
consistency; it does not prove source provenance or protect against concurrent edits.
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
for exact expected results.

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
No feedback is sent automatically.

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
These tasks use bundled synthetic inputs.

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


### Optional repeat-review manifest (prototype)

For a repeat review, save pairs as data in a UTF-8 JSON file instead of repeating
command triples. The bundled `examples/batch.json` uses invented inputs:

```sh
status=0
python3 evaluation/batch-manifest.py --totals examples/batch.json './manifest reports' || status=$?
printf 'Manifest batch status: %s\n' "$status"
cat './manifest reports/status.tsv'
cat './manifest reports/totals.json'
```

Expected status: 1, pair-0001 changed and pair-0002 equal. Relative CSV paths are
relative to the manifest's containing directory (including when invoked from a
different directory); absolute paths are allowed. The new report directory is
relative to your current working directory. Use a new name for each run.
For a symlinked manifest, the containing directory means the path you supplied,
not the symlink target's directory. Paths may include `..`; this is not a sandbox.
Use only your authorized local files and a trusted report directory.

The schema is exactly `{"version":1,"pairs":[{"before":"before.csv",
"after":"after.csv","key":"id"}]}`. Version must be integer 1. There must be
1–100 pairs and at most 65,536 manifest bytes. Duplicate/unknown/missing fields,
empty strings, control characters, Unicode surrogates, invalid UTF-8/JSON and
nonregular manifests are refused with status 2 before report creation. Strings
retain spaces, Unicode and exact key spelling; paths receive no environment,
`~`, wildcard or shell expansion. The manifest cannot supply commands or options.
It does not install code or make network calls.

Optional `--totals`, `--ignore-column COLUMN` and `--max-input-bytes N` are supplied
on the command line before the manifest, with the same batch meanings. Use
`--ignore-column=-name` for a column starting with a dash. After valid manifest
parsing, missing/invalid CSVs remain per-pair status 2, later pairs continue,
and totals are partial. Files are read anew on every run: a manifest does not
pin CSV contents. Preserve the original CSV snapshots alongside your reports.
It provides no concurrent-edit protection or provenance verification. Python
3.10+ and a POSIX shell are required; Windows/macOS remain untested. This optional
workflow has synthetic Linux tests.


#### Manifest refusal diagnostics

Validation failures return status 2 with a fixed code and an action, without
printing the supplied path, JSON content or exception text. Validation finishes
before the batch runner starts, so a malformed manifest creates no report directory.

| Code | Action |
| --- | --- |
| `E_ARGUMENTS` | Check options; supply a manifest and, unless validating only, a report directory. |
| `E_BUDGET` | Use an input budget from 1 to 10485760 bytes. |
| `E_READ` | Check manifest existence and read permission. |
| `E_FILE` | Supply a regular file; regular-file symlinks are allowed. |
| `E_SIZE` | Reduce the manifest to at most 65536 bytes. |
| `E_ENCODING` | Save as UTF-8. |
| `E_BOM` | Create a separate UTF-8 copy without its leading BOM in the same directory; see [recovery step 6](RECOVERY.md#6-recover-a-manifest-exported-with-a-leading-utf-8-bom). |
| `E_JSON` | Fix JSON syntax and remove NaN/Infinity constants. |
| `E_DEPTH` | Reduce structural JSON nesting to at most 32 levels. |
| `E_DUPLICATE` | Remove duplicate object fields. |
| `E_SCHEMA` | Use exactly top-level version and pairs fields. |
| `E_VERSION` | Use integer version 1. |
| `E_PAIRS` | Supply 1–100 pairs in a list. |
| `E_PAIR` | Use exactly before, after and key in each pair. |
| `E_TEXT` | Use nonempty strings without controls or surrogates. |
| `E_RUNNER` | Check shell availability; the runner could not be launched. |

Codes describe the first detected problem; fix it and validate again. Once the
runner starts, its own existing output and status rules apply. These diagnostics
are not a privacy guarantee for subprocess output or a filesystem sandbox.

### Manifest preflight without comparisons

```sh
python3 evaluation/batch-manifest.py --validate-only examples/batch.json
```

For automation, add `--json` (requires `--validate-only`):

```sh
python3 evaluation/batch-manifest.py --validate-only --json examples/batch.json
```

Stdout is one JSON object with `version: 1`, `valid`, fixed `code`,
`pair_count`, `csv_files_checked: false` and `reports_created: false`.
Success returns 0 with code `OK` and the validated pair count. Refusal returns 2,
with a fixed `E_*` code and `pair_count: null`; the fixed human diagnostic also
appears on stderr. No supplied paths, keys or content appear in this metadata.
A valid manifest can still reference missing or invalid CSVs. JSON mode does not
create reports, even if a report-directory argument is supplied. `--json` without
`--validate-only` refuses before execution. Use full option names; abbreviations
are refused. `--help` retains ordinary help output. This stdout privacy contract
does not cover operating-system/interpreter failures or the separate execution
runner's output.


Preflight checks the same full manifest schema, limits, encoding and literal
path/key resolution as execution. Success prints only the number of pairs and
returns 0; a refusal uses the fixed reason diagnostic and returns 2. No CSV is
opened or checked, no batch runner is launched, and no report directory is
created. Missing CSVs therefore do not fail preflight. This does not establish
that a comparison will succeed or that inputs will remain unchanged.
An optional report-directory argument is ignored in this mode, including an
existing directory; it is still required for normal execution. Budget and
ignore-column options are validated; totals has no effect until execution.

For a literal missing-CSV preflight, failed execution and preserved retry, follow
[RECOVERY.md, steps 4–5](RECOVERY.md#4-separate-manifest-preflight-from-csv-execution).


### Automate preflight and handle execution separately

Run this synthetic walkthrough from the inner `csv-change-report` directory with
Python 3.10+ and a POSIX shell. It creates its own temporary CSVs/manifests, consumes
JSON metadata and process exit status, then compares only accepted manifests.
It does not read your CSVs or make network calls. Temporary reports are removed
when the block exits; use a trusted persistent directory for your own reports.

```sh
python3 - <<'PYCODE'
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

def require(condition, message):
    if not condition:
        raise SystemExit(message)

runner = Path('evaluation/batch-manifest.py').resolve()
require(runner.is_file(), 'Run from the inner csv-change-report directory')
with tempfile.TemporaryDirectory(prefix='csv-json-walkthrough-') as temporary:
    work = Path(temporary)
    (work / 'before.csv').write_text('id,value\n1,old\n', encoding='utf-8')
    (work / 'after.csv').write_text('id,value\n1,new\n', encoding='utf-8')
    def manifest(after):
        return json.dumps({'version': 1, 'pairs': [
            {'before': 'before.csv', 'after': after, 'key': 'id'}]})
    cases = [
        ('changed', manifest('after.csv'), 0, 'OK', 1),
        ('equal', manifest('before.csv'), 0, 'OK', 0),
        ('malformed', '{', 2, 'E_JSON', None),
        ('missing-csv', manifest('absent.csv'), 0, 'OK', 2),
    ]
    for name, document, expected_preflight, expected_code, expected_run in cases:
        source = work / (name + '.json')
        source.write_text(document, encoding='utf-8')
    originals = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in work.iterdir() if p.is_file()}
    for name, _, expected_preflight, expected_code, expected_run in cases:
        source = work / (name + '.json')
        reports = work / (name + '-reports')
        preflight = subprocess.run(
            [sys.executable, str(runner), '--validate-only', '--json', str(source)],
            capture_output=True, text=True, check=False)
        # Unexpected interpreter/OS output fails closed: never launch comparison.
        metadata = json.loads(preflight.stdout)
        expected = {'version': 1, 'valid': expected_preflight == 0,
                    'code': expected_code,
                    'pair_count': 1 if expected_preflight == 0 else None,
                    'csv_files_checked': False, 'reports_created': False}
        require(preflight.returncode == expected_preflight,
                'Unexpected preflight exit status')
        require(type(metadata) is dict and metadata.keys() == expected.keys()
                and all(type(metadata[key]) is type(value)
                        and metadata[key] == value
                        for key, value in expected.items()),
                'Unexpected preflight metadata')
        require(not reports.exists(), 'Preflight unexpectedly created reports')
        print(f'{name}: preflight={preflight.returncode} code={metadata["code"]}')
        if preflight.returncode != 0 or metadata['valid'] is not True:
            print('  execution skipped; no reports')
            continue
        # Preflight success permits comparison; it does not predict its result.
        run = subprocess.run([sys.executable, str(runner), str(source), str(reports)],
                             capture_output=True, text=True, check=False)
        require(run.returncode == expected_run, 'Unexpected comparison exit status')
        require((reports / 'status.tsv').is_file(), 'Missing comparison status.tsv')
        print(f'  execution={run.returncode}; status.tsv created')
    require(all(hashlib.sha256(p.read_bytes()).hexdigest() == digest
                for p, digest in originals.items()), 'Original fixture bytes changed')
    print('Original fixture bytes preserved; temporary reports removed on exit.')
PYCODE
```

Expected: `changed` preflight 0/OK then execution 1 (differences);
`equal` preflight 0/OK then execution 0 (no retained differences);
`malformed` preflight 2/E_JSON with execution skipped; `missing-csv` preflight
0/OK then execution 2 (input error). Execution 0 means no retained differences,
1 means differences, and 2 means an error; inspect `status.tsv` before using
partial reports. Preflight 0 never proves CSV existence or content validity.
The explicit checks remain active with optimized Python (`-O` or
`PYTHONOPTIMIZE=1`). They check these fixtures; this is not a general production
wrapper. Metadata fields must match the expected values and JSON value types.
Unexpected or non-JSON preflight output stops this block before comparison.
Execution output has its own privacy limits; this example captures it without
printing supplied paths or CSV content. Files may change after preflight; no
concurrent-edit protection is provided. Tested on Linux only.

### Standalone checked batch automation

From the extracted product directory, run:

```sh
status=0
python3 evaluation/automate-batch.py evaluation/sample-manifest.json './automated reports' || status=$?
printf 'Automation status: %s\n' "$status"
```

Use an existing manifest in place of `evaluation/sample-manifest.json` if needed;
see the manifest format above. The report directory must be new and its parent
must exist. The helper also runs from other working directories when you supply
its path and your manifest/report paths. Manifest CSV paths remain relative to
the manifest directory. Python 3.10+ and the bundled POSIX shell runner are needed.

Exit status is 0 for equal, 1 for changed and 2 for error. A single JSON object on
stdout contains version=1, code, status and pair_count (null when preflight was
not accepted). Codes: EQUAL, CHANGED, E_COMPARISON (completed with pair errors),
E_ARGUMENTS, E_PREFLIGHT, E_OUTPUT (report path already exists),
E_EXECUTION (unexpected runner exit), E_STATUS (missing,
incomplete, malformed or inconsistent status table). `--help` prints ordinary
usage text. Full option names are required; use `--` before positional arguments
that start with a dash.

The helper checks exact successful preflight field types, executes only accepted
preflight, then checks complete status-table counts and agreement with execution.
Preflight does not check CSV contents. Reports and per-pair diagnostics remain in
the requested directory; existing directories are refused. Failures before a
complete table produce E_STATUS; an existing report path produces E_OUTPUT. The
helper captures child stdout/stderr without echoing paths or CSV values; inspect
preserved diagnostics locally. Interpreter/OS launch failures before this script
starts are outside that output contract. There is no automatic cleanup or resume.
Preserve failed runs and use a different new directory after correction.

This is an offline example for a trusted local directory. It does not authenticate
helpers/reports, prevent concurrent edits, provide crash durability, or approve
exports. A changed manifest between preflight and execution can invalidate the
preflight observation. Table validation does not verify report bytes. Reports
retain the privacy limits described above. Tested with synthetic inputs on Linux; Windows/macOS are untested.

### Run the automation regressions

From the inner `csv-change-report` directory, run:

```sh
python3 -m unittest -v test_automate_batch
python3 -O -m unittest -v test_automate_batch
```

These offline synthetic tests use temporary CSV fixtures and report directories.
They check equal and mixed batches, error precedence and continuation, preservation
of existing outputs, invalid manifests and arguments, and missing or file-valued
output parents. Two POSIX permission tests first observe a real directory-creation
denial; they skip explicitly on other platforms or when the runtime bypasses
permissions (for example, root). They check denied-parent failure, preservation of
read-only existing reports, and subsequent use of a fresh writable directory.
Optimized suite runs also pass optimization to the wrapper subprocess. An
output-parent failure currently returns `E_STATUS` because no complete status
table exists. Disk faults, concurrent edits and crash recovery are untested.
The suite uses only Python's
standard library; the batch runner also requires the shell tools listed above.

### Offline column tally

After generating a JSON report, run:

```sh
python3 evaluation/column-tally.py /path/to/report.json
python3 -m unittest -v test_column_tally
```

The helper accepts detailed format 1 and summary format 2 reports up to 16 MiB.
It emits sorted column names, changed-cell counts per column, their sum, and the
changed-record count. Added/removed records are excluded from these cell counts;
ignored/key columns are absent. One changed record may affect several columns.
Exit 0 means a tally was produced (including a changed report); exit 2 means an
unreadable, oversized, malformed or inconsistent report. Errors use fixed text.
Input bytes are preserved. It opens only the specified JSON, with no CSV or network
access. Cell values are not copied, but column names remain visible and may be
sensitive. JSON escaping keeps control characters escaped. Validation checks
count types and arithmetic, not report authenticity or agreement with source CSVs.
Untrusted reports can forge valid counts or put arbitrary text in column names.

Optional batch column counts (offline, report-only):

```sh
python3 evaluation/batch-totals.py /path/to/status.tsv --expected-pairs 3 --column-counts
```

`column_tally` sums changed cells and changed records across successful reports,
with sorted column names and a count of included reports. Failed pairs are
excluded even if stale report files exist. `partial: true` means errors or
unfinished pairs were excluded; an empty tally does not imply a successful run.
Exit status remains 0 for equal, 1 for changed, 2 for errors/incomplete runs.
An unreadable or invalid successful report fails with no JSON totals.
Combine with `--row-counts` when row totals are also wanted. Added/removed rows
are excluded from column counts, so an added-only batch can have zero changed
cells. No CSV is opened or cell values copied. Column names remain visible.
Counts and status tables are not authenticated; reports from different schemas
combine identical column names. Concurrent report mutation is not supported.

Column grouping is by the exact case-sensitive name only, with no schema or
pair identifier. Compared columns with no changes remain present with a zero
count. For example, `amount` changed once in each of two different
schemas is emitted once with `changed_cells: 2`; this does not establish that
the two fields have the same meaning or units. Run separate batch summaries
for unrelated schemas when that distinction matters. No schema-aware grouping
option is provided. Names are JSON data (control characters are escaped), not
paths to open. Status-table report and diagnostic fields must match the exact
generated pair filenames; absolute, parent-relative and alternate names are
rejected with exit 2 and no totals, including with `--column-counts`.
