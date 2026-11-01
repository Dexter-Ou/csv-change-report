# Choose a report for an offline review

This free 0.1.10-preview needs an existing Python 3.10+ installation. Extract the
ZIP and enter its inner `csv-change-report` directory. Linux synthetic command
checks are available; Windows/macOS remain untested.
No install, account or network is needed to run. Examples below are invented.

| Your task | Choose | What it leaves out |
| --- | --- | --- |
| Read counts and changed record positions in a terminal | Text | Input hashes and old/new values |
| Keep positions and reproducible input hashes | Default JSON | Old/new values |
| See counts before deciding where to investigate | Summary JSON | Record positions and old/new values |
| Review several pairs | Batch helper | Positions; use a separate detailed comparison |

All reports can reveal column names and counts; JSON also reveals hashes.
They are not anonymized. If you need old/new values, inspect your original
snapshots locally. Input must be comma-separated UTF-8 with matching column sets
and one nonblank unique key per record. UTF-8 with or without a leading BOM and
LF or CRLF record endings are supported. BOM and record-ending differences alone
do not count as data changes, but the raw input hashes can differ. Other formats
need a different tool.

For a repository-readable tour, see [the report and batch preview](PREVIEW.md).

## Try three views of the same synthetic change

These commands print reports and return 0 on successful comparisons, even when
changes exist. None writes a report file or edits the inputs.

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --format text
python3 csv_change.py examples/before.csv examples/after.csv --key id
python3 csv_change.py examples/before.csv examples/after.csv --key id --summary-only
```

Each reports 3 records before and after: 1 added, 1 removed, 1 changed, 1 unchanged.
Text and detailed JSON locate the changed `status` at before/after record 1,
the addition at after record 2 and removal at before record 2. Summary omits
those positions. Record numbers count parsed data records, excluding the header.
Compare `examples/expected-report.json` for the detailed answer key.

## Save a detailed report for later review

From the same directory, choose a new filename in a trusted local directory:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --output saved-review.json
```

A successful save returns 0 and prints nothing. Open `saved-review.json` in a
local text editor: `changed_records` points to before/after record 1 and names
`status`; `added_after_records` and `removed_before_records` each contain 2.
Use each position with its corresponding original snapshot. Positions are parsed
data records, not physical line numbers: a quoted cell can span multiple lines.
The report omits key and cell values, so inspect those records in your originals
to see what changed. Check `before_sha256` and `after_sha256` against the snapshots
when you need to confirm which input bytes the report describes.

An existing destination is refused with status 2 and left intact. Keep that report
and choose a new filename for another run. Report-file writes require hard links;
a pre-link write failure normally leaves no destination. Cleanup failure can
leave a complete report with error status 2. Preserve failed-run evidence and
follow [output recovery](evaluation/OUTPUT-FAILURE.md). Avoid shell redirection onto inputs.

## Check statuses before automating

`--check` changes successful exit status to 0=equal, 1=changed; errors are 2.
Use this block to handle expected status 1, including inside a `set -e` shell:

```sh
status=0
python3 csv_change.py examples/before.csv examples/after.csv --key id --check --summary-only || status=$?
printf 'Check status: %s\n' "$status"
```

Expected check status: 1. It means review changes, not comparison failure.
For an equal example replace AFTER with `examples/before.csv` (status 0).
For an invalid example use `evaluation/duplicate-key.csv` (status 2, no report).
Never interpret an error as equality or export approval.

## Bound raw reads for a batch

For a ready-to-run example with equal, changed and invalid pairs, follow
[the synthetic mixed-batch example](examples/mixed-batch/README.md). It includes
expected index labels and row counts; both commands intentionally return 2
because one comparison fails.

This block requires a POSIX shell. Run once with an unused output directory;
keep previous results and choose a new name on retry. The parent must exist.

```sh
status=0
sh evaluation/batch-review.sh --max-input-bytes 4096 './quickstart reports' examples/before.csv examples/after.csv id || status=$?
printf 'Batch status: %s\n' "$status"
cat './quickstart reports/status.tsv'
```

Expected batch status: 1, with pair-0001 status 1 and a summary JSON report.
Place the optional byte budget first; omit it for the default 10 MiB per input.
An over-budget input returns 2 with no JSON report. This is a raw-read limit,
not a total-memory guarantee. Batch errors take precedence over changed status.

## Open a local index of the saved batch

After the batch command has returned and all writers have stopped, run:

```sh
status=0
python3 evaluation/batch-index.py './quickstart reports' --expected-pairs 1 || status=$?
printf 'Index status: %s\n' "$status"
```

Expected index status: 1 for this changed pair. Open
`quickstart reports/index.html` locally to follow its JSON summary and diagnostic
links. An empty diagnostic is normal for a successful pair. This page does not
show old/new cell values or generate per-pair HTML comparison views.

Supply the original expected pair count, including failed or unfinished pairs;
counting saved rows can hide missing work. Status 2 means review required or
creation refused: inspect the message and saved files. An existing index is
preserved. Keep the whole stopped report directory together when copying or
archiving it so the relative links still reach their files. Use trusted local
directories; the index does not verify CSV provenance or concurrent writes.
The count must be 1–100, the table at most 64 KiB, and each linked summary at
most 1 MiB. See [the index guide](evaluation/BATCH-INDEX.md) for limits and
[recovery instructions](evaluation/RECOVERY.md) before a fresh-directory retry.
Browser interaction and accessibility remain untested.

For a runnable recovery walkthrough, follow [the simulated stopped-batch example](examples/interrupted-batch/README.md). It preserves a synthetic stopped directory and reruns into a fresh one; it does not interrupt or resume a real process.

For your own authorized snapshots, quote paths, replace the key exactly and
preserve originals. Avoid shell redirection onto inputs. See [the full rules](README.md)
for limits, exclusive `--output`, optional exclusions and recovery, and
[the evaluation kit](evaluation/README.md) for mixed batches and safe retries.
Do not share private files or reports in public issues. These examples use synthetic data.

Report-file output requires filesystem hard links. Status 2 can retain a complete
report after temporary cleanup failure; see [output recovery](evaluation/OUTPUT-FAILURE.md).

HTML viewer output also requires hard links. Cleanup failure may leave complete
HTML with status 2; see [viewer output recovery](VIEWER.md#html-output-failures-and-recovery).

## Troubleshoot blank or repeated keys

Follow the [stable-key example](examples/stable-key/README.md) to reproduce
blank-key and duplicate-key errors, then compare source-corrected fictional
exports and create a source-checked HTML report.

## Local shell automation

Follow the [local shell recipe](examples/automation/README.md) to branch on
`--check` statuses 0 (unchanged), 1 (changed), and 2 (invalid input), including
a caller using `set -eu`. The recipe runs locally and creates no reports.

Inventory workflow: [review stock changes and resolve an invalid ID](examples/inventory-reconciliation/README.md). Uses fictional exports.
