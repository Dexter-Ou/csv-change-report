# 0.1.10-preview batch report validation

Batch review validates JSON summary structure, row/column counts and consistency
with comparator status before recording a successful comparison. Missing,
malformed, incomplete or inconsistent reports record status 2 and report `-`;
retained files are diagnostic evidence, not completed results. Later pairs still
run, and optional totals exclude failed pairs and mark partial results.

Ninety-eight focused synthetic Linux checks passed, including malformed reports,
status contradictions, genuine comparisons and mixed batches, with and without
totals. The suite passed 59 unittest methods. Twenty-six prior synthetic output
fault checks also passed. These checks do not prove CSV provenance or safety
under concurrent directory edits. Windows/macOS remain untested.

Use a trusted new output directory and preserve failed runs. No dependency
installation is required. See evaluation/README.md for batch and recovery rules.
CLI version remains 0.1.10-preview.
