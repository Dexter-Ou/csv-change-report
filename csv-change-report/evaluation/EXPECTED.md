# Synthetic answer key

For `examples/before.csv` to `examples/after.csv`: three records on each side;
one added (after record 2), one removed (before record 2), one changed (before
record 1 to after record 1, column `status`), one unchanged. Record positions
exclude the header and count parsed records, not physical lines. The complete
JSON oracle is `examples/expected-report.json`. The raw CLI with `--check` exits
1; `review.sh` prints the change notice and exits 0 after handling it.

Comparing `examples/before.csv` with itself: zero added/removed/changed, three
unchanged. Raw CLI and wrapper both exit 0; wrapper prints the no-change notice.

Comparing the before fixture with `evaluation/duplicate-key.csv`: error, raw CLI
and wrapper exit 2. No completed report; stderr contains the fixed duplicate-key
diagnostic and wrapper failure notice. Neither snapshot should change.

These fixtures validate mechanics only. They do not establish that a real user
can find relevant changes or would pay. Header/row reordering alone does not
count as a keyed content change; a changed key is a removal plus addition.


## Volatile-field exercise (raw CLI)

All three comparisons have two records per input and zero added/removed keys.
Without exclusions, `volatile-before.csv` to `volatile-only.csv` has two changed,
zero unchanged, and column totals `exported_at: 2`; `--check` exits 1.

With `--ignore-column exported_at`, the same pair has zero changed, two unchanged,
zero changed-cell totals for retained columns, `ignored_columns: ["exported_at"]` and exit 0.
Both full-input SHA-256 values still describe different original bytes.

With that same exclusion, `volatile-before.csv` to `retained-change.csv` has one
changed, one unchanged, column totals `status: 1` and exit 1. The changed record
has key B2, before/after record position 2, and changed columns ["status"]. The
status changed from pending to active in the original synthetic snapshots.

No command modifies input snapshots. A workflow that excludes `status` too would
hide that meaningful change; choosing exclusions is the reviewer's decision.
These are synthetic mechanical examples, not independent user feedback.

## Summary-versus-detail exercise

Both changed-pair reports have before=3, after=3, added=1, removed=1,
changed=1, unchanged=1, column totals name=0 and status=1, and the same
full-input hashes. Both `--check` statuses are 1. Summary JSON has
format_version=2 and report_mode="summary"; detailed JSON keeps format_version=1.
Summary omits added_after_records, removed_before_records and changed_records
entirely. Detailed output locates the addition at after record 2, removal at
before record 2 and status change at before/after record 1. The summary alone
cannot locate these records. Neither output reveals old/new cell values.

Self-comparison summary has before=3, after=3, unchanged=3, all change counts
and column totals zero; status 0. Duplicate-key comparison has no report,
fixed JSON diagnostic on stderr and status 2. Text summary retains counts and
column totals but no per-record locations; JSON retains full-input hashes.

## Mixed-batch interpretation

Batch status 2 means at least one error, not that every pair failed. The complete
three-row table has pair-0001 status 0 and pair-0001.json, pair-0002 status 1 and
pair-0002.json, pair-0003 status 2 and report `-`. The invalid pair has no JSON
report; inspect pair-0003.stderr for the fixed repeated-key diagnostic. No usable
comparison result exists for that pair. Do not interpret it as equality.

The changed pair is the second BEFORE/AFTER/KEY triple: examples/before.csv,
examples/after.csv, id. Its summary counts are before=3, after=3, added=1,
removed=1, changed=1, unchanged=1. The separate detail command exits 1 and retains
those counts and both full-input hashes. It locates addition at after record 2,
removal at before record 2 and changed column status at before/after record 1.
Summary omits these locations. The detail report is a separate file and does not
change the table or summary. Repeating the detail command against its existing
output exits 2 and preserves that file. Neither report contains old/new values.
Pair-0003 requires input correction based on domain knowledge, then a new batch
report directory; this exercise deliberately leaves it unresolved.
