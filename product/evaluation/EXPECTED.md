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

Header/row reordering alone does not
count as a keyed content change; a changed key is a removal plus addition.
