# Review an inventory export change

Fictional stock records for a technical operations user. This example compares
exports; it does not update inventory or decide whether a stock movement is valid.
Requires Python 3.10+. From the product folder containing csv_change.py, run each
command separately. Use a fresh output name on repeat runs.

## Stop when the key column is missing

If either export lacks the exact `stock_id` header, the comparison exits 2 with
`key column is missing` and creates no report. Check the header in both exports:
`--key stock_id` is case-sensitive and spaces are significant. Keep the original
files unchanged. Ask the source system administrator for an export containing
the confirmed unique record identifier; do not invent IDs or substitute SKU,
which repeats across bins in this example. If the source uses a different header,
confirm that it identifies the same records in both exports before changing
`--key` to that exact name. Retry with the source-confirmed exports and a fresh
output name. The supplied `after-corrected.csv` is fictional example data, not a
repair for a real export.

## Stop on ambiguous identity

```sh
python3 csv_change.py examples/inventory-reconciliation/before.csv examples/inventory-reconciliation/after-invalid.csv --key stock_id --output invalid-inventory.json
```

Expected: exit 2, stderr includes `record 2 repeats a key`, no report created.
The NORTH and EAST records share S-101 in this invalid export. SKU is also
repeated across bins and is unsuitable as the key. Do not discard the second row
or assign a guessed ID to get past validation. Preserve the original export and
ask the source system administrator to confirm the record identity.

## Compare a source-confirmed correction

In this fictional scenario, the source confirms EAST is S-103. The supplied
`after-corrected.csv` represents a new corrected export; the invalid file remains
unchanged. In real work, obtain source evidence before using a corrected export.

```sh
python3 csv_change.py examples/inventory-reconciliation/before.csv examples/inventory-reconciliation/after-corrected.csv --key stock_id --output inventory-report.json
python3 view_report.py inventory-report.json --before-csv examples/inventory-reconciliation/before.csv --after-csv examples/inventory-reconciliation/after-corrected.csv --output inventory-report.html
python3 csv_change.py examples/inventory-reconciliation/before.csv examples/inventory-reconciliation/after-corrected.csv --key stock_id --check
```

Expected: first two commands exit 0; last exits 1 (changes found).
Open inventory-report.html locally to review positions and changed columns.
The report contains positions and column names, not stock IDs or cell values.
Use those positions to inspect the original CSV records:

| Finding | CSV data record position | Source review |
| --- | --- | --- |
| Quantity changed | before 1, after 1 | S-101 quantity 10 to 8; verify movement |
| Removed | before 2 | S-102 absent; check whether export scope changed |
| Unchanged | before 3, after 2 | S-103 remains 7 |
| Status changed | before 4, after 3 | S-104 held to available; verify release |
| Added | after 4 | S-105 quantity 4; verify new stock record |

Counts: 4 before, 4 after, 1 added, 1 removed, 2 changed, 1 unchanged.
Record positions exclude the header and count CSV records, not physical lines.
Exact text comparison means numeric formatting can register as a change.
A missing record is not proof of deletion; export scope may differ. Matching
source hashes verify bytes, not business truth. Never automate stock adjustments
from these findings alone. Keep originals and retain reports with their inputs.

The JSON and HTML are offline artifacts. Interactive browser layout and
accessibility have not been tested.
