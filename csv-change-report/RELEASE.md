# 0.1.10-preview batch output fixes

Batch review guards status-file writes, per-pair stream setup and comparator
execution. Missing or empty regular reports cannot be recorded as successful
comparisons. Output failures return error 2. Optional totals retain partial
results when individual comparisons fail; inspect status.tsv before using them.

Twenty-six synthetic per-pair checks passed on Linux, with and without totals,
and both runs passed 53 unittest methods. Injected filesystem faults and
controlled comparator wrappers are synthetic tests, not a guarantee against
concurrent directory edits. Windows/macOS remain untested.

Documentation describes the offline workflow, prerequisites and limitations.
No dependency installation is required. See evaluation/README.md for full
batch/recovery rules. CLI version remains 0.1.10-preview.
