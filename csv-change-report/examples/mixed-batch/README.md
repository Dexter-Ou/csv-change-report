# Try a mixed batch offline

These invented CSVs demonstrate equal, changed and invalid comparisons. They are
synthetic examples, not customer exports.

Requires Python 3 and the extracted product; no install or network is needed.
From the `csv-change-report` directory, run each command separately:

```sh
python3 evaluation/automate-batch.py examples/mixed-batch/manifest.json mixed-batch-reports
python3 evaluation/batch-index.py mixed-batch-reports --expected-pairs 3
```

Both commands intentionally exit with status **2** because pair 3 repeats a key.
Do not join them with `&&`: the second command must run after the first stops.
The first prints `E_COMPARISON`; that is the planned invalid-input case.

Open `mixed-batch-reports/index.html` locally after both commands stop.
Expected rows, in manifest order (counts are added / removed / changed / unchanged):

| Pair | Label | Counts |
| --- | --- | --- |
| 1 | EQUAL | 0 / 0 / 0 / 3 |
| 2 | CHANGED | 1 / 1 / 1 / 1 |
| 3 | ERROR — comparison failed | Unavailable / Unavailable / Unavailable / Unavailable |

Review-required guidance is expected. The third diagnostic explains the duplicate
key; Unavailable does not mean zero. Changed counts are rows, not changed cells.
The page links saved summaries and diagnostics, not per-pair HTML views.

Keep the first report directory as a snapshot. To repeat, use a fresh directory
name in both commands; existing outputs are preserved and creation is refused.
Do not edit status rows to hide errors. Use trusted directories with all writers
stopped. When trying private exports, keep exports, reports and diagnostics private.
Index limits: original expected count 1–100, status table at most 64 KiB,
summary at most 1 MiB. See evaluation/BATCH-INDEX.md and evaluation/RECOVERY.md.
Browser interaction/accessibility, Windows/macOS and crash durability are untested.
