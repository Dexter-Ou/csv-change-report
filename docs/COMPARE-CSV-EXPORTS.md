# Compare CSV exports by ID instead of line number

A line diff is useful for text edits. When a CSV export changes its row order,
matching records by a stable ID answers a different question: which records
were added, removed or changed?

CSV Change Report compares UTF-8 comma-separated snapshots locally with Python
3.10+ and no third-party packages. It reports counts, record positions and
changed column names without including cell values. It is a free MIT-licensed
preview. [Download and run the synthetic example](../README.md#download-to-your-first-report).

## Choose the comparison that answers your question

| Question | Approach |
| --- | --- |
| Which literal lines changed? | A text diff |
| Which records changed despite row or column reordering? | Compare by a stable unique key |
| Did numeric values change within a tolerance? | Use a tool with numeric/tolerance rules; this tool compares exact strings |
| Which values changed, or which rows should be merged? | Use a value diff/merge tool; this report omits cell values and never merges inputs |

## Try one export review

After extracting the download, open a terminal in the inner `csv-change-report`
folder. The included fixtures are synthetic. Run:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --check
```

The command returns **1**, meaning changed compared content. Expect 3 records
in each file: 1 added, 1 removed, 1 changed and 1 unchanged. The changed column
is `status`; the report locates it at record 1 in each input. Record positions
exclude the header. The after fixture also reorders the columns; that alone
does not count as a change. For the full expected JSON, see
[`examples/expected-report.json`](../csv-change-report/examples/expected-report.json).

For a readable terminal summary:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --format text --check
```

This also returns 1. These expected nonzero results can stop scripts using
`set -e`; handle comparison statuses deliberately.

## Apply it to your snapshots

Choose a key that is present, unique, nonblank and stable in both exports.
Replace the example paths and `id` in the command with your authorized inputs.
Keep the original snapshots. A key change is counted as a removal and an
addition; it is not inferred to be a rename. Duplicate or blank keys are errors.

Comparisons are exact and case-sensitive. Whitespace, formatting such as `01`
versus `1`, and changed timestamps count as changes. Row or header reordering
alone is equal. Both files must have matching column sets. See the
[comparison rules and options](../csv-change-report/README.md) before deciding
whether to ignore any columns: ignoring a column changes what equality means.

With `--check`, status 0 means equal, 1 means changed, and 2 means error.
Without `--check`, a successful changed comparison returns 0. Inspect stderr
when status is 2; output failures also return 2. Save reports only to a fresh
path in a trusted directory using `--output`; shell redirection onto an input
can destroy it before Python runs. A failed write can leave a partial file.
[Preserve evidence and retry safely](../csv-change-report/evaluation/RECOVERY.md).

## Limits and sharing

Tested on Linux; Windows and macOS are untested. Each input is limited to
10 MiB, 50,000 records, 256 columns and 250,000 data cells. Inputs and reports
remain in memory; these are not a hostile-input memory guarantee. There is no
network upload, telemetry or formula evaluation. Reports still expose column
names, counts, positions and input hashes; hashes are not anonymization.
Review reports before sharing. Use [batch workflows](../csv-change-report/evaluation/README.md)
for repeated comparisons. No response or support turnaround is promised.
