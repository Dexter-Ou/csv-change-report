# Reproduce a 10,000-row inventory comparison

Requires Python 3.10 or newer; no packages, account or service. Extract this folder, open a terminal in it, then run:

```sh
python3 generate_inventory.py "demo data"
python3 csv_change.py "demo data/before.csv" "demo data/after.csv" --key stock_id --output "demo data/report.json"
python3 view_report.py "demo data/report.json" --before-csv "demo data/before.csv" --after-csv "demo data/after.csv" --output "demo data/report.html"
python3 csv_change.py "demo data/before.csv" "demo data/reordered.csv" --key stock_id --output "demo data/reordered.json" --check
```

Open `demo data/report.html` locally to inspect the report. No browser interaction or accessibility test is claimed. The final command exits 0: reordering alone does not change keyed records.

Expected report counts: before 10,000; after 10,000; added 100; removed 100; changed 300; unchanged 9,600. The generator removes S00000–S00099, increases quantity for S00100–S00299, puts S00300–S00399 on hold, adds S10000–S10099, then reverses the export. Quantity changes total 200 cells; status changes total 100. These are fictional records and a synthetic correctness example, not customer data or a performance guarantee.

Each input has five columns and 50,000 cells, below the tools' 50,000-row, 250,000-cell and 10-MiB per-input limits. This does not test maximum capacity. Reports identify record positions and changed column names, not business correctness. Source hashes check exact input bytes. Counts, positions, columns and hashes can still expose sensitive metadata: keep real exports and reports private.

The generator refuses an existing directory; tools refuse existing report files. To repeat, choose a new directory and adjust all paths. Keep outputs until no longer needed. If interrupted, choose a fresh directory; partial output is not a completed comparison. Do not remove your own data to make the example run. JSON `--check` returns 1 when changes exist, 0 when none exist, and 2 on errors.

`SHA256SUMS` lists SHA-256 digests for the other five supplied files. On systems providing sha256sum, run `sha256sum -c SHA256SUMS` before generating data. A matching manifest detects changed bytes; it does not prove publisher identity. Tools and example use the included MIT license.
