# CSV Change Report

Compare two CSV exports by a stable unique key, offline, without uploading data.
The JSON or optional text report locates added, removed and changed records and names changed
columns without including cell values. Free, MIT-licensed preview from Gong LLC.

## Download and run the tested preview

Requires an existing Python 3.10+ installation; standard library only. No package
installation, account, API key or network connection is needed to run the tool.
Python 3.12.15 on Linux has been tested; Windows/macOS have not been tested.

1. [Download the complete tested source ZIP](https://codeload.github.com/Dexter-Ou/csv-change-report/zip/efebadd1e3514a239f060b2a5ec37bb7d151193a).
   This link pins the synthetic-tested code, rather than following future edits.
2. Extract it into a new folder. Open a terminal in the extracted outer folder
   named `csv-change-report-efebadd1e3514a239f060b2a5ec37bb7d151193a`.
3. Enter its inner product folder and run the included synthetic example:

```sh
cd csv-change-report
python3 --version
python3 csv_change.py --version
python3 csv_change.py examples/before.csv examples/after.csv --key id
```

Expect `counts` to contain `before: 3`, `after: 3`, `added: 1`, `removed: 1`,
`changed: 1`, `unchanged: 1`; the changed record is before/after record 1 and
its changed column is `status`. Record numbers exclude the header.
The complete expected JSON is in `examples/expected-report.json`.

Optional acceptance checks, from the same inner folder:

```sh
python3 -m unittest -v
python3 csv_change.py --help
python3 -m unittest -v test_column_tally
```

One hundred two synthetic test methods passed on the isolated Linux worker. These are
synthetic software checks, not an assurance for hostile inputs.
If your Python installation uses a different command, use its Python 3 command.

For your own files, replace both paths and the key column name:

```sh
python3 csv_change.py /path/to/before.csv /path/to/after.csv --key id
```

Use copies of snapshots you are authorized to process. Do not redirect output
onto either input: the shell can truncate it before the tool runs. Successful
comparisons exit 0 by default even when changes exist; errors exit 2 with JSON on stderr.
Add `--check` for local scripts: exit 1 means added, removed or changed keyed
records; exit 0 means equal content. Row/header reordering alone is equal.
The report is still produced. Output errors take precedence and exit 2; check
the status even if a report file looks complete. See the full product rules
for a shell example that handles all three statuses.
For command errors, consult `--help`; the error deliberately omits supplied text.

For a terminal summary without input hashes, add `--format text`:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --format text
```

Text shows the same counts and record locations, with quoted column names and
per-column change counts. Unicode and control characters in column names are
escaped. JSON remains the default; `--format json` selects it explicitly.
Both formats omit cell values and paths; errors remain JSON on stderr.

Save directly to a new file with `--output report.json`, or combine
`--format text --output report.txt`. Existing paths and input-path collisions
are refused; successful file output leaves stdout empty. On Linux new report
permissions are owner-only. A write failure may leave a partial new report;
inspect it and use a new name when retrying. Use a trusted output directory.

## Choose a report

Follow the [short report-choice guide](csv-change-report/QUICKSTART.md) for terminal text, detailed JSON, summary JSON and batch reports. Its three literal shell blocks passed on a fresh pinned Linux download.

## Fit and limits

UTF-8 comma-separated CSV only; matching column sets and one nonblank unique key
per record. Exact, case-sensitive comparisons, no trimming or type inference.
A changed key counts as a removal plus an addition. Limits per input: 10 MiB,
50,000 records, 256 columns and 250,000 data cells. Both inputs and the report
are held in memory; these limits are not an adversarial resource guarantee.

Reports expose column names, counts, record positions and input hashes; review
before sharing. Hashes are not anonymization. No network, telemetry or formula
evaluation. Preserve original files and version information for recovery.
See the [full product rules](csv-change-report/README.md),
[release notes](csv-change-report/RELEASE.md) and [license](csv-change-report/LICENSE).
This repository is downloadable source, not a hosted application.

## Offline evaluation kit

From the inner `csv-change-report` folder, try:

```sh
sh evaluation/review.sh examples/before.csv examples/after.csv id
sh evaluation/review.sh examples/before.csv examples/before.csv id
sh evaluation/review.sh examples/before.csv evaluation/duplicate-key.csv id
```

The wrapper handles the raw CLI's expected change status 1: changed and equal
comparisons both exit 0 after a notice; invalid input exits 2. See the
[task and recovery steps](csv-change-report/evaluation/README.md),
[synthetic answer key](csv-change-report/evaluation/EXPECTED.md) and
[voluntary feedback prompts](csv-change-report/evaluation/FEEDBACK.md).
The tested public kit passed the 59-method suite and the changed-export journey on Linux
Python 3.12.15 with synthetic fixtures.
Use the inner `csv-change-report/evaluation` directory; the separate top-level
`product/evaluation` directory is a superseded misplaced draft, not runnable.

## Optional five-minute feedback task

If you voluntarily want to evaluate the preview, run the included example before
using any real data. Can you locate
which record changed, which column changed, and where the added record appears?
Then compare your answer with the expected JSON. Skip any question you prefer.

You may voluntarily open an issue in this repository with only:

- Your operating system, Python version and tool `--version` output; did download-to-example succeed?
- Where you got stuck and roughly how long the task took.
- Whether you could interpret the changed/added/removed record positions.
- A recurring export-review task this might help, or why it would not help.

Do not upload CSV files, reports, private paths, customer names, credentials or
other sensitive material. Issues are public. No response or support turnaround is promised. No telemetry is collected by the tool.

Version 0.1.7-preview fixes stdout write/flush failures and preserves exit 2 for
closed pipes. It cannot confirm downstream receipt or storage of report bytes.


Version 0.1.7-preview adds repeated `--ignore-column NAME` selections for volatile
non-key fields. Exact names only; unknown/key fields fail closed. Reports list
exclusions; original full-byte hashes and validation remain. Added/removed keys
still count. With `--check`, status 0 means equality among compared fields.
For example, append `--ignore-column status` to the included example: changed
becomes 0, unchanged becomes 2, and added/removed remain 1 each. Full schemas
must still match. Without exclusions, content is unchanged apart from version.
The candidate also passed 256 seeded synthetic CLI checks against an independent
list-based oracle.

The refreshed evaluation kit includes timestamp-only and retained-status changes.
Its shell-safe raw CLI examples demonstrate --check statuses 1, 0, 1 when
exported_at is explicitly excluded from the latter two comparisons. See the
[evaluation task](csv-change-report/evaluation/README.md) and answer key.
Fresh public extraction passed 36 synthetic test methods, six JSON/text exercise
comparisons, the documented shell block, two invalid exclusions and three wrapper
journeys on Linux Python 3.12.15 with synthetic fixtures.


Version 0.1.8-preview adds `--summary-only` for JSON and text. It omits record
positions and per-record changed-column lists while retaining counts and column
totals. JSON retains full-input hashes and uses format_version 2 with report_mode
summary; default detailed JSON remains version 1. `--check` statuses are unchanged.
Both input snapshots remain in memory.
On a synthetic 10,000-record changed diff, JSON shrank from 1,138,301 to 453 bytes;
text from 378,026 to 203 bytes. This measures output size, not runtime performance.

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --summary-only
```

The offline evaluation kit now includes a summary-versus-detail exercise with
counts, omitted locations and explicit check statuses 0/1/2. Its documented
changed-pair commands also passed under `sh -ec` with synthetic fixtures.

The offline evaluation kit includes `evaluation/batch-review.sh` for several
export pairs. It writes numeric summary reports and per-pair status rows into
a new directory, continues after invalid pairs and refuses existing directories.
Five synthetic batches (11 pairs), documented commands and 40 existing tests
passed on the candidate and fresh public extraction. See the inner evaluation README for run and failure recovery steps.

The offline kit includes a mixed-batch interpretation exercise: distinguish errors
from changed pairs, then locate changes in a separate detailed report.

Offline batch totals are available in `evaluation/batch-totals.py`; follow the evaluation guide and supply your original expected pair count to detect missing rows.

Practice preserving a stopped batch and retrying into a new directory with the
[offline recovery exercise](csv-change-report/evaluation/RECOVERY.md). Its stopped
snapshot is simulated; process interruption and crash durability are untested.


Version 0.1.9-preview accepts `--max-input-bytes N` (1..10485760) for a smaller
per-input raw byte budget. The default remains 10 MiB. Encoded bytes, header, BOM
and line endings count. Exactly N bytes may pass; N+1 is refused before report
creation. This is not a total-memory bound. The batch helper defaults to the same ceiling; a leading budget option is available below.

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --max-input-bytes 4096
```

The pinned public download passed 53 synthetic unittest methods, this byte-budget
example and the three evaluation wrapper journeys on the isolated Linux worker.



Version 0.1.10-preview adds a leading optional per-input byte budget to batch review:

```sh
sh evaluation/batch-review.sh --max-input-bytes 4096 './budget reports' examples/before.csv examples/after.csv id
```

Use an unused report directory. Expected status 1 means changed; inspect status.tsv
and pair reports. Status 2 indicates an error. The helper continues after a failed
pair; an existing directory is refused. The default remains 10 MiB per input.
Canonical decimal budgets 1..10485760 are accepted before directory creation.
See the evaluation guide for retry and interpretation steps. This bounds raw input
reads, not total process memory. The pinned public extraction passed 53 synthetic
unittest methods and this command on Linux.


The pinned download also includes an optional complete reader exercise. After
entering the inner product folder, start at [evaluation/READER-START.md](csv-change-report/evaluation/READER-START.md).
It includes a six-task worksheet and a separate answer key. Fresh public Linux
extraction matched all 29 candidate files and passed the four literal setup/guide
shell blocks using synthetic fixtures.


Try the [worked timestamp-export recipe](csv-change-report/evaluation/TIMESTAMP-RECIPE.md)
to compare baseline and deliberately filtered counts using invented records. The
pinned download includes it; its literal shell block and expected output passed
on the isolated Linux worker. Ignoring timestamps reduced changed records from
two to one while preserving one addition and one removal. 

The offline batch helper now accepts one `--ignore-column COLUMN` for every
pair, together with its byte budget in either option order. See the
[evaluation guide](csv-change-report/evaluation/README.md#optional-batch-ignored-column)
for a worked timestamp-only versus meaningful-change batch. Candidate and fresh
pinned public downloads passed 53 existing tests and 16 additional synthetic
checks on Linux.


For optional batch aggregate row counts, use `--totals` as described in the
[evaluation guide](csv-change-report/evaluation/README.md#optional-aggregate-row-counts).
It writes pair outcomes and summed added/removed/changed/unchanged rows to
`totals.json`. Failed pairs are excluded and explicitly mark results partial;
any pair error still returns status 2. Candidate and fresh pinned public source
each passed 53 existing tests and 11 focused synthetic checks on Linux, including
the literal recipe. 


Optional batch totals now require a regular temporary output file and return
status 2 for output, rename or cleanup failures. Candidate and pinned public
Linux tests covered nine synthetic cases and 53 existing unittest methods.
Equal/changed batches retain status 0/1; mixed error batches retain partial totals
and status 2. Fault injection does not prove safety under hostile directory edits.

Batch status-file initialization and append failures now return error 2 with an incomplete-batch diagnostic. Existing pair reports after a failed run are not proof of a complete batch. Five injected status-write faults and three normal batch cases passed on the candidate; fault injection is synthetic Linux evidence.

Batch review validates version 2 JSON summaries, row and column counts, and agreement with comparator exit status before recording status 0 or 1. Malformed or inconsistent reports record error 2 and report `-`; later pairs continue. Ninety-eight focused synthetic checks and 59 unittest methods passed on Linux, plus 26 prior output-fault checks. Validation checks report structure and internal consistency; it does not prove source provenance or protection from concurrent edits.


Repeat an offline batch with a data-only JSON manifest using
`evaluation/batch-manifest.py`; see the [manifest example and rules](csv-change-report/evaluation/README.md#optional-repeat-review-manifest-prototype).
Relative CSV paths use the manifest directory. The revised suite passed 66
unittest methods on synthetic Linux inputs, including exact path/key handling,
manifest refusal and equivalence to explicit triples. The pinned download and
its five literal guide/setup/manifest shell blocks were checked on Linux.
Windows/macOS and hostile concurrent edits remain untested.


Manifest validation refusals now include fixed reason codes and recovery actions,
without printing supplied paths or JSON contents. Argument errors also use fixed
text. Structural JSON nesting is limited to 32 levels. Validation refusals create
no report directory; once the batch runner starts, its usual output rules apply.
See the [diagnostic reference](csv-change-report/evaluation/README.md#manifest-refusal-diagnostics).
The candidate and pinned public extraction each passed 69 synthetic Linux unittest
methods, including refusal codes and no-output checks. The unavailable-shell case
uses fault injection. All five literal guide/setup/manifest shell blocks passed.


Validate a batch manifest without running comparisons using `--validate-only`.
It checks the schema and resolves literal paths without opening CSV files or
creating reports; missing CSVs still require a normal run to detect. See the
[preflight example](csv-change-report/evaluation/README.md#manifest-preflight-without-comparisons).
The candidate and pinned public download passed 71 synthetic Linux unittest
methods, including no-runner and no-report checks. Windows/macOS remain untested.


Follow the [manifest recovery walkthrough](csv-change-report/evaluation/RECOVERY.md#4-separate-manifest-preflight-from-csv-execution) to distinguish successful manifest preflight from a missing CSV during execution, preserve a failed attempt and retry with a corrected manifest in a new report directory. All six literal recovery blocks and 71 regression methods passed with synthetic Linux fixtures on the candidate and pinned download.

Leading UTF-8 BOM manifests receive fixed `E_BOM` guidance. Follow [recovery step 6](csv-change-report/evaluation/RECOVERY.md#6-recover-a-manifest-exported-with-a-leading-utf-8-bom) to preserve the original and create a separate same-directory copy. Candidate checks passed 73 synthetic Linux unittest methods and both new literal recovery blocks; Windows/macOS remain untested.

For scripts, `--validate-only --json` emits versioned metadata with a fixed code and pair count, without reading CSV files or creating reports. Refusals use status 2 and a null pair count. See the [JSON preflight instructions](csv-change-report/evaluation/README.md#manifest-preflight-without-comparisons). The candidate and pinned public extraction each passed 78 synthetic Linux unittest methods, including metadata privacy and no-execution checks. Windows/macOS remain untested.

For a runnable example that consumes JSON preflight metadata and handles comparison
status separately, see [the automation walkthrough](csv-change-report/evaluation/README.md#automate-preflight-and-handle-execution-separately).

The walkthrough covers equal CSVs (execution 0), changed CSVs (1), malformed
manifests (execution skipped), and missing CSVs (2). All four literal branches
passed on the candidate and pinned download with synthetic Linux fixtures.

Run checked preflight, comparison and complete status-table checks with
`python3 evaluation/automate-batch.py evaluation/sample-manifest.json "./automated reports"`
from the inner product folder. This bundled two-pair sample returns status 1;
0 means equal and 2 means an error. The report path must be new.
See [standalone automation](csv-change-report/evaluation/README.md#standalone-checked-batch-automation)
for fixed JSON codes, preserved diagnostics and limits.

Run the bundled automation regressions with `python3 -m unittest -v test_automate_batch`
from the inner product directory; see [the test instructions](csv-change-report/evaluation/README.md#run-the-automation-regressions).
