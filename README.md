# CSV Change Report

Compare two CSV exports by a stable unique key, offline, without uploading data.
The JSON report locates added, removed and changed records and names changed
columns without including cell values. This free MIT-licensed preview is an
experiment by Gong LLC. Usefulness and willingness to pay remain unverified.

## Download and run the tested preview

Requires an existing Python 3.10+ installation; standard library only. No package
installation, account, API key or network connection is needed to run the tool.
Python 3.12.15 on Linux has been tested; Windows/macOS have not been tested.

1. [Download the complete tested source ZIP](https://codeload.github.com/Dexter-Ou/csv-change-report/zip/f4a14b2b8a34bb4fe123494003c5cfbbde959f95).
   This link pins the synthetic-tested code, rather than following future edits.
2. Extract it into a new folder. Open a terminal in the extracted outer folder
   named `csv-change-report-f4a14b2b8a34bb4fe123494003c5cfbbde959f95`.
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

Eighteen synthetic test methods passed on the isolated Linux worker. These are
software checks, not customer validation or an assurance for hostile inputs.
If your Python installation uses a different command, use its Python 3 command.

For your own files, replace both paths and the key column name:

```sh
python3 csv_change.py /path/to/before.csv /path/to/after.csv --key id
```

Use copies of snapshots you are authorized to process. Do not redirect output
onto either input: the shell can truncate it before the tool runs. Successful
comparisons exit 0 even when changes exist; errors exit 2 with JSON on stderr.
For command errors, consult `--help`; the error deliberately omits supplied text.

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
