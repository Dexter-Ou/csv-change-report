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

## Reproduce row-order and changed-key behavior

From the same inner folder, save the following as `try_export_keys.py` in a
fresh trusted location and run `python3 try_export_keys.py`. It creates three
temporary synthetic CSVs and removes them when finished. It needs no download
beyond the existing product. Existing inputs are never used or modified.

```python
import json
from pathlib import Path
import subprocess
import sys
import tempfile

# Run from the inner csv-change-report folder; all CSVs below are synthetic.
with tempfile.TemporaryDirectory(prefix="csv-order-example-") as directory:
    folder = Path(directory)
    fixtures = {
        "before": "id,status\na,open\nb,closed\nc,open\n",
        "reordered": "id,status\nc,open\nb,closed\na,open\n",
        "changed-key": "id,status\nz,open\nb,closed\nc,open\n",
    }
    for name, content in fixtures.items():
        (folder / (name + ".csv")).write_text(content, encoding="utf-8")
    cases = [
        ("reordered", 0, {"added": 0, "removed": 0, "changed": 0, "unchanged": 3}),
        ("changed-key", 1, {"added": 1, "removed": 1, "changed": 0, "unchanged": 2}),
    ]
    for name, status, expected in cases:
        result = subprocess.run(
            [sys.executable, "csv_change.py", str(folder / "before.csv"),
             str(folder / (name + ".csv")), "--key", "id", "--check"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if result.returncode != status or result.stderr:
            raise RuntimeError(f"{name}: unexpected status or diagnostic: {result.stderr}")
        counts = json.loads(result.stdout)["counts"]
        if any(counts.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"{name}: unexpected counts: {counts}")
        print(name, "status", result.returncode, json.dumps(expected, sort_keys=True))
```

Expected output:

```text
reordered status 0 {"added": 0, "changed": 0, "removed": 0, "unchanged": 3}
changed-key status 1 {"added": 1, "changed": 0, "removed": 1, "unchanged": 2}
```

The wrapper exits 0 only when both checks pass. The child comparison's changed
status 1 is expected and explicitly checked. The key `a` becoming `z` produces
an addition and removal even though its other cell is identical. This does not
establish identity across changed keys; choose a stable key for real exports.

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
