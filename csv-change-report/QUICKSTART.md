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
and one nonblank unique key per record. Other formats need a different tool.

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

For your own authorized snapshots, quote paths, replace the key exactly and
preserve originals. Avoid shell redirection onto inputs. See [the full rules](README.md)
for limits, exclusive `--output`, optional exclusions and recovery, and
[the evaluation kit](evaluation/README.md) for mixed batches and safe retries.
Do not share private files or reports in public issues. These examples use synthetic data.
