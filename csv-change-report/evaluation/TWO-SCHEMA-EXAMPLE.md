# Compare column tallies across two schemas

Run this synthetic example from the extracted `csv-change-report` directory with
Python 3.10+ and a POSIX shell. No network or installation is needed.
The first pair tracks invoice amounts; the second tracks stock quantities.
Both call their changing field `amount`, but those fields have different units.

Use a trusted local directory. The commands create a new `two-schema-demo`
directory and refuse to reuse it; choose a fresh name throughout to run again.
They do not overwrite existing reports or modify the input snapshots.

```sh
(umask 077; mkdir './two-schema-demo') || exit 2
printf 'id,amount,currency\n1,10,USD\n' > './two-schema-demo/invoices-before.csv'
printf 'id,amount,currency\n1,12,USD\n' > './two-schema-demo/invoices-after.csv'
printf 'sku,amount,unit\nA,3,each\n' > './two-schema-demo/stock-before.csv'
printf 'sku,amount,unit\nA,4,each\n' > './two-schema-demo/stock-after.csv'
status=0
sh evaluation/batch-review.sh './two-schema-demo/reports' \
  './two-schema-demo/invoices-before.csv' './two-schema-demo/invoices-after.csv' id \
  './two-schema-demo/stock-before.csv' './two-schema-demo/stock-after.csv' sku || status=$?
[ "$status" -eq 1 ] || exit 2
cat './two-schema-demo/reports/status.tsv'
status=0
python3 evaluation/batch-totals.py './two-schema-demo/reports/status.tsv' \
  --expected-pairs 2 --column-counts --pair-column-counts || status=$?
[ "$status" -eq 1 ] || exit 2
```

Both comparisons contain changes, so both tools return status 1. The checks
handle that expected status even in a shell using `set -e`; status 2 is an error.
The table identifies `pair-0001` as invoices and `pair-0002` as stock, in argument
order. Keep that mapping alongside the reports: the generated pair ID does not
encode a schema, filename, unit or business meaning.

In the JSON totals, expect:

- `partial` is `false`; both pairs completed successfully with changes.
- `column_tally.changed_cells` is `2`, with `amount` counted twice.
  `currency` and `unit` remain present with zero changed cells.
- `pair_column_tallies` has two entries. Each has `changed_records: 1` and
  `changed_cells: 1`. For `pair-0001`, `amount` is 1 and `currency` is 0;
  for `pair-0002`, `amount` is 1 and `unit` is 0.

The merged count means two cells named `amount` changed. It does not add their
values, convert units or mean that two dollars or two stock units changed.
Per-pair tallies preserve the separation; they do not infer schema relationships.
Added and removed records are excluded from these changed-cell counts.

The totals helper reads the status table and successful JSON reports, not the
CSV snapshots. Cell values are not copied into totals; column names remain
visible. Counts are not authenticated. Check errors, incomplete counts and the
`partial` flag on other batches. Use trusted directories; symlink confinement,
hostile concurrent changes, crashes and disk faults are unsupported or untested.
This example is checked on Linux; other platforms have not been verified.
