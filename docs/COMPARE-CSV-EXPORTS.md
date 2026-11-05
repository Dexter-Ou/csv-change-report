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

## Save a report and open it as HTML

To inspect the output first, [download a saved synthetic HTML example](examples/README.md).
The example note explains how to open it locally and what its metadata means.

Use the [pinned preview download](https://github.com/Dexter-Ou/csv-change-report/archive/a38d2a40f42e2c944335df8174cd915c8a129e72.zip)
for this walkthrough. After extracting it, enter the inner `csv-change-report`
folder. Choose a trusted writable directory with hard-link support and fresh
output names. Run each command separately:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --check --output export-review.json
python3 view_report.py export-review.json --before-csv examples/before.csv --after-csv examples/after.csv --output export-review.html
```

The comparison returns **1** for the expected changes and saves JSON; this is
not an error. The viewer returns **0** and saves HTML. If automating, accept
comparison status 0 or 1 before invoking the viewer; stop on 2. Do not connect
these two commands with `&&`, which would skip the viewer after status 1.

Open `export-review.html` in your local browser. Expect the same counts as above
and `status` as the changed column, with before/after record positions 1.
The explicit CSV arguments also check their bytes against the saved hashes;
this does not prove report provenance or correctness. The viewer reads saved
JSON rather than recomputing the comparison. Keep the JSON and original CSVs.

Existing output paths are refused with status 2 and preserved. A viewer output
error can leave complete HTML and a temporary sibling if cleanup fails; status
2 is not success even when HTML exists. Preserve stderr and failed-run files,
inspect the trusted directory, and use a fresh output name after correcting the
cause. See [HTML output recovery](../csv-change-report/VIEWER.md#html-output-failures-and-recovery)
for the cleanup diagnostics. Do not redirect output over an input file.

HTML has no scripts or external resources, but still exposes report metadata.
Review it before sharing. JSON over 8 MiB is refused. The commands have synthetic
Linux coverage; interactive browser appearance, accessibility and Windows/macOS
behavior are untested. For aggregate-only HTML or other viewer options, see the
[viewer guide](../csv-change-report/VIEWER.md).

## Review inventory exports with ambiguous IDs

For a complete stock-export walkthrough, follow the [fictional inventory review](https://github.com/Dexter-Ou/csv-change-report/blob/a38d2a40f42e2c944335df8174cd915c8a129e72/csv-change-report/examples/inventory-reconciliation/README.md).
It starts with a duplicate stock ID, stops without creating a report, then uses
an export whose record identity was confirmed by the fictional source system.
The corrected comparison finds 1 added, 1 removed, 2 changed and 1 unchanged
record. It also shows how to save JSON and HTML and locate the affected records
in the source snapshots.

Use the pinned preview download above; the fixtures are in
`examples/inventory-reconciliation` inside the product folder. Keep the original
exports. Do not guess a replacement ID or automate stock adjustments from a
change report: missing records may reflect export scope, and source hashes
verify bytes rather than business truth.

## Open a ready-made inventory report offline

[Open the fictional inventory example instructions](../examples/inventory-review/README.md)
for a saved HTML/JSON review, source CSVs, unchanged command-line tools and a
SHA-256 manifest. [Download the source archive](https://codeload.github.com/Dexter-Ou/csv-change-report/zip/325b4bfead4ee874ec762c5e551fe3ed4267b399), extract it, then
open `examples/inventory-review/inventory-report.html` locally. Python is needed
only to reproduce the report. The example includes an invalid duplicate ID and
a corrected export; all data is fictional. Review sensitive metadata before
sharing reports. Interactive browser layout and accessibility are untested.

## Generate a 10,000-row inventory example

[Follow the reproducible inventory recipe](../examples/inventory-scale/README.md)
to generate fictional exports, compare them by stock ID and save JSON/HTML.
The expected synthetic result is 100 added, 100 removed, 300 changed and 9,600
unchanged records. A reorder-only export compares equal. The folder includes
the tools, generator, license and SHA-256 manifest; Python 3.10+ is required,
with no third-party packages. [Download the source archive](https://codeload.github.com/Dexter-Ou/csv-change-report/zip/e0fe51f6e0f4fa6d6c3216bcc3e2107eb00eeea9).
Extract it and enter `examples/inventory-scale` before following the commands.
This is a correctness example within documented limits, not a maximum-capacity
or performance guarantee. Keep real exports and report metadata private.

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

## Compare two build artifacts manually

Obtain the CSV artifacts from the two revisions through your own authorized
build process, and keep them in separate local folders. Confirm that both
exports cover the same scope and use the same schema and stable unique key.
CSV Change does not build revisions, fetch artifacts or post PR comments.

From the inner `csv-change-report` folder, use the current download linked
above. Replace the quoted paths and `id` with your actual inputs. Choose fresh
report names in a trusted writable directory with hard-link support. Run these
commands separately:

```sh
python3 csv_change.py "before build/export.csv" "after build/export.csv" --key id --check --output build-review.json
python3 view_report.py build-review.json --before-csv "before build/export.csv" --after-csv "after build/export.csv" --output build-review.html
```

Run the viewer only after comparison status 0 (equal) or 1 (changed); stop on
status 2 and inspect stderr. A changed comparison saves JSON while returning 1,
so `&&` would skip the viewer. Existing output names are refused; use fresh
names for each review rather than overwriting reports.

Open the HTML locally. It lists changed columns and record positions, not old
or new cell values. To review values, retain both original artifacts and locate
the records using a CSV parser: embedded newlines make physical line numbers
unsuitable. Record positions are one-based data records, excluding the header.
The viewer checks supplied originals against the report's hashes; byte matches
do not authenticate the report or establish that the builds were correct.
Review metadata before sharing. This is a manual local review; it does not
attach reports to a PR or automate CI.

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
