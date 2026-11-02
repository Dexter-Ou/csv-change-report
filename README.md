# CSV Change Report

Compare two CSV exports by a stable unique key, offline, without uploading data.
Find added, removed and changed records and the columns that changed, without
including cell values. Free, MIT-licensed preview from Gong LLC.

## Download to your first report

Requires Python 3.10+; standard library only. No installation, account, API key
or network connection is needed to run. Tested on Linux with Python 3.12.15;
Windows and macOS have not been tested.

1. [Download the tested source ZIP](https://codeload.github.com/Dexter-Ou/csv-change-report/zip/15a6465483ae34e93dc030937d5b276ad5424303).
2. Extract into a new folder and open a terminal in the outer
   `csv-change-report-15a6465483ae34e93dc030937d5b276ad5424303` folder.
3. Run the included synthetic example:

```sh
cd csv-change-report
python3 --version
python3 csv_change.py --version
python3 csv_change.py examples/before.csv examples/after.csv --key id
```

Expect counts of 3 before, 3 after, 1 added, 1 removed, 1 changed and 1 unchanged.
The changed record is record 1 in both inputs; its changed column is `status`.
Record numbers exclude the header. Compare with `examples/expected-report.json`.
If your installation uses a different Python 3 command, substitute that command.

From the same inner folder, show a shorter terminal report:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --format text
```

For your own authorized snapshots, replace both paths and `id` with your key
column. Keep originals. JSON is the default; add `--output report.json` to save
to a new file. Existing paths and input collisions are refused. Never redirect
shell output onto either input: the shell can truncate it before the tool runs.
Use a trusted output directory with hard-link support. Pre-link write faults normally
leave no destination; temporary cleanup failure can leave a complete report with
error status 2. Preserve failed-run evidence and follow
[output recovery](csv-change-report/evaluation/OUTPUT-FAILURE.md) before retrying.
New report files have owner-only permissions on tested Linux.

Comparisons exit 0 by default even when changes exist. Add `--check` in scripts:
0 means equal compared content, 1 means changed, 2 means an error. Row/header
reordering alone is equal. Output errors take precedence and return 2; a report
that looks complete is not proof of success. Errors use JSON on stderr.


HTML viewer output also requires hard links. Cleanup failure may leave complete
HTML with status 2; see [viewer output recovery](csv-change-report/VIEWER.md#html-output-failures-and-recovery).

## More workflows

- [Run six synthetic terminal examples with automatic checks](https://github.com/Dexter-Ou/csv-change-report/tree/15a6465483ae34e93dc030937d5b276ad5424303/examples/terminal-walkthrough). Download that revision, then run `python3 examples/terminal-walkthrough/run_tour.py` from the extracted outer folder.

- [Review a fictional inventory export and resolve an invalid stock ID](https://github.com/Dexter-Ou/csv-change-report/blob/a38d2a40f42e2c944335df8174cd915c8a129e72/csv-change-report/examples/inventory-reconciliation/README.md).

- [Fix blank or duplicate CSV keys with a worked example](csv-change-report/examples/stable-key/README.md).
- [Compare CSV exports by ID instead of line number](docs/COMPARE-CSV-EXPORTS.md).
- [Choose text, detailed JSON, summary or batch reports](csv-change-report/QUICKSTART.md).
- [Full options, comparison rules and scripting examples](csv-change-report/README.md).
- [Batch manifests, validation, ignored columns and aggregate totals](csv-change-report/evaluation/README.md).
- [Worked timestamp-export recipe](csv-change-report/evaluation/TIMESTAMP-RECIPE.md).
- [Preserve failed batches and retry safely](csv-change-report/evaluation/RECOVERY.md).
- [Optional offline reader exercise](csv-change-report/evaluation/READER-START.md).
- [Release notes](csv-change-report/RELEASE.md) and [MIT license](csv-change-report/LICENSE).

Use the inner `csv-change-report/evaluation` directory. The separate top-level
`product/evaluation` directory is a superseded draft and is not runnable.

## Fit, privacy and limits

UTF-8 comma-separated CSV only, with matching column sets and a nonblank unique
key per record. Comparisons are exact and case-sensitive, without trimming or
type inference. A changed key counts as a removal plus an addition. Ignoring a
column changes what equality means; schema and key validation still apply.

Per input: at most 10 MiB, 50,000 records, 256 columns and 250,000 data cells.
A smaller raw-byte budget is optional. Inputs and reports remain in memory;
these limits do not guarantee bounded memory or safety for hostile inputs.
Hostile concurrency, symlink confinement, atomicity and crash/disk faults have
not been tested. Batch tools require a POSIX shell.

Reports expose column names, counts and, depending on mode, record positions and
input hashes. Review before sharing; hashes are not anonymization. The tool has
no network calls, telemetry or formula evaluation. Preserve source snapshots
and tool version for recovery. This is downloadable source, not a hosted app.

## Optional feedback

Try the synthetic example before real data. If you choose to open a public issue,
include your OS, Python/tool versions, whether setup worked, where you got stuck,
and any missing capability relevant to your export-review workflow.
Do not upload CSVs, reports, private paths, customer names, credentials or other
sensitive material. No response or support turnaround is promised.
