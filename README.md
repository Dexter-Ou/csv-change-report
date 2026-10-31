# CSV Change Report

Compare two CSV exports by a stable unique key, offline, without uploading data.
The JSON or optional text report locates added, removed and changed records and names changed
columns without including cell values. This free MIT-licensed preview is an
experiment by Gong LLC. Usefulness and willingness to pay remain unverified.

## Download and run the tested preview

Requires an existing Python 3.10+ installation; standard library only. No package
installation, account, API key or network connection is needed to run the tool.
Python 3.12.15 on Linux has been tested; Windows/macOS have not been tested.

1. [Download the complete tested source ZIP](https://codeload.github.com/Dexter-Ou/csv-change-report/zip/edcc8f8f72d550354164366075de9180e8c0d8a7).
   This link pins the synthetic-tested code, rather than following future edits.
2. Extract it into a new folder. Open a terminal in the extracted outer folder
   named `csv-change-report-edcc8f8f72d550354164366075de9180e8c0d8a7`.
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
```

Thirty-six synthetic test methods passed on the isolated Linux worker. These are
software checks, not customer validation or an assurance for hostile inputs.
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
The tested public kit passed the 36-method suite and the changed-export journey on Linux
Python 3.12.15. These are synthetic checks, not usability or customer evidence.
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
other sensitive material. Issues are public. No response, support turnaround or
payment is promised. No telemetry is collected by the tool. Owner/internal tests
will be recorded separately from independent volunteer feedback. No independent
feedback, customer acceptance or revenue has yet been established.

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
list-based oracle; these tests do not establish user demand or revenue.

The refreshed evaluation kit includes timestamp-only and retained-status changes.
Its shell-safe raw CLI examples demonstrate --check statuses 1, 0, 1 when
exported_at is explicitly excluded from the latter two comparisons. See the
[evaluation task](csv-change-report/evaluation/README.md) and answer key.
Fresh public extraction passed 36 synthetic test methods, six JSON/text exercise
comparisons, the documented shell block, two invalid exclusions and three wrapper
journeys on Linux Python 3.12.15. These are internal tests, not user feedback.
