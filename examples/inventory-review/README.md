# Fictional inventory review — offline example

Unzip this folder and open inventory-report.html locally. It is a pre-generated
example, not your inventory. All records are fictional. Python 3.10+ is required
only to reproduce it. No installation or network service is required.
Interactive browser layout and accessibility have not been tested.

From this folder on Linux, verify the included file bytes:

```sh
sha256sum -c SHA256SUMS
```

This manifest detects accidental changes; it is not a signature or independent
proof of origin. The comparison engine is unchanged from CSV Change preview
0.1.10 at product revision a38d2a40f42e2c944335df8174cd915c8a129e72.
The included viewer matches the source archive's csv-change-report/view_report.py
and adds links to report sections. SHA256SUMS records the exact included bytes.
Historical comparison source:
https://github.com/Dexter-Ou/csv-change-report/tree/a38d2a40f42e2c944335df8174cd915c8a129e72/csv-change-report

Run these commands separately to reproduce the JSON and HTML. Use fresh output
names on repeat runs; existing reports are never overwritten.

```sh
python3 csv_change.py before.csv after-corrected.csv --key stock_id --output reproduced.json
python3 view_report.py reproduced.json --before-csv before.csv --after-csv after-corrected.csv --output reproduced.html
```

Both exit 0. Reproduced files should match inventory-report.json and
inventory-report.html exactly. To check saved hashes directly before rendering:

```sh
python3 view_report.py inventory-report.json --before-csv before.csv --after-csv after-corrected.csv --output verified.html
```

Expected exit 0. An altered source returns exit 2 with E_SOURCE and creates no
HTML. Matching hashes check bytes only, not business truth or correctness of
the reported changes. Keep reports and original exports together.

To see the ambiguous-key failure:

```sh
python3 csv_change.py before.csv after-invalid.csv --key stock_id --output invalid.json
```

Expected exit 2, record 2 repeats a key, no invalid.json created. In this fictional
scenario the source confirmed EAST is S-103 in after-corrected.csv. Never invent
replacement IDs or discard duplicate rows to force a comparison.

## Review against original CSV records

Positions count CSV data records excluding the header, not physical lines.

| Finding | Position | Fictional source review |
| --- | --- | --- |
| Quantity changed | before 1, after 1 | S-101: 10 to 8; verify movement |
| Removed | before 2 | S-102 absent; check export scope |
| Unchanged | before 3, after 2 | S-103 remains 7 |
| Status changed | before 4, after 3 | S-104 held to available; verify release |
| Added | after 4 | S-105 quantity 4; verify new record |

Counts: 4 before, 4 after, 1 added, 1 removed, 2 changed, 1 unchanged.
Missing records are not proof of deletion. Exact text comparison may detect
numeric formatting differences. Do not automate stock adjustments from reports.

## Sensitive metadata

JSON/HTML omit CSV cell values but retain counts, column names, positions and
source hashes; those can still be sensitive. This folder deliberately includes
fictional source CSVs. Never use it as a template for publishing private exports.
Review reports and manifests before sharing. HTML contains no script or external
resources; it does not validate business truth. Source CSVs may change after a
hash comparison. Other platforms remain untested.

MIT license for the included tools is in LICENSE.
