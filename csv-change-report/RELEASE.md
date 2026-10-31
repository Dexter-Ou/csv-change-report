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


## Optional JSON batch manifests

Repeat an offline batch using `evaluation/batch-manifest.py` and a JSON list of
before/after/key triples. Relative CSV paths use the manifest directory; report
paths use the current directory. See evaluation/README.md and examples/batch.json.
Malformed manifests are refused before reports are created. After parsing,
per-pair errors and partial totals retain the existing batch behavior.
Batch keys beginning with a dash are now passed literally to the comparator.

The revised suite passed 66 unittest methods on Linux with synthetic inputs,
including manifest boundaries, path/key handling and explicit-triple equivalence.
The CLI version remains 0.1.10-preview. Windows/macOS and hostile concurrent
writes remain untested.
