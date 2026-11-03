# 0.1.11-preview: compound CSV keys

Repeat `--key NAME` to compare rows by an exact combination of columns.
Blank components, duplicate tuples, repeated column names and ignored key
components are rejected. Single-key calls and JSON report formats remain
compatible. Compound keys work in the comparator and generated zipapp; batch
manifest schema remains single-key. Linux/Python 3.12.15 synthetic comparator,
viewer and packaging journeys were exercised. Windows/macOS remain untested.

# Stable-key troubleshooting example

Adds four fictional CSV fixtures and runnable steps for blank and repeated key
errors, source correction, JSON comparison and source-checked HTML review.
Runtime behavior and CLI version remain unchanged.

# Optional breaks in long HTML text

The HTML viewer inserts inert optional break elements in long ASCII words,
including column labels and hashes. Reconstructed text and escaping are
preserved by synthetic parser tests; Unicode words remain intact. CSP is
unchanged. Actual browser layout, clipboard behavior, screen readers and
accessibility conformance have not been tested. CLI version stays 0.1.10-preview.

# Failure-safe HTML viewer output

HTML writes now use a private temporary sibling and no-clobber hard link.
Pre-link write failures normally leave no requested HTML. Cleanup failure keeps
status 2 and explicit committed/cleanup-required diagnostics. Hard-link support
is required. See VIEWER.md for recovery and permanent regression commands.
CLI version remains 0.1.10-preview. Crash durability and other platforms are
untested; no browser appearance or accessibility claim is added.

# Failure-safe report output

Report-file writes use a private temporary sibling
and no-clobber hard-link publication. Pre-link write faults normally leave no
requested destination. Cleanup failure retains conservative error 2 and explicit
committed/cleanup-required diagnostics. Batch handling remains conservative.
See evaluation/OUTPUT-FAILURE.md for requirements, regressions and manual recovery.
Hard-link support is required; crash durability and other platforms are untested.
CLI version remains 0.1.10-preview.

# JSON manifest preflight

Adds `--validate-only --json` with versioned fixed-code metadata and validated
pair count. Refusals retain status 2, fixed stderr and null count. No CSV read or
report creation occurs in preflight. Full option names are now required.
Synthetic Linux tests cover metadata privacy, malformed manifests, argument
errors, missing CSVs and no execution; other platforms remain untested.

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


## Actionable manifest refusals

Manifest validation now emits fixed reason codes and recovery actions without
including supplied paths, JSON contents or exception messages. Command argument
errors also use fixed text. JSON nesting is limited to 32 structural levels;
brackets inside JSON strings do not count. Validation refusals create no report
directory. After validation, the batch runner retains its existing output rules.

The revised suite passed 69 unittest methods on synthetic Linux inputs, including
all refusal categories, no-output assertions, 32/33-level nesting boundaries and
quoted brackets. The unavailable-shell case uses fault injection. CLI version
remains 0.1.10-preview; Windows/macOS and hostile concurrent edits are untested.


## Offline manifest preflight

Use `--validate-only` to validate and resolve a manifest without launching the
batch runner or creating reports. CSV existence and contents are not checked;
normal execution still requires a new report directory. See evaluation/README.md.


## Manifest recovery walkthrough

RECOVERY.md steps 4–5 show a schema-valid manifest with a missing CSV, partial
execution totals and a separate corrected manifest/new report directory. Both
attempts remain available for review. Commands use synthetic fixtures; Linux
execution is checked. No CSV existence check was added to preflight.

Leading UTF-8 BOM manifests now receive fixed E_BOM guidance. Strict refusal is retained; evaluation/RECOVERY.md documents a separate same-directory copy. Synthetic Linux tests cover refusal privacy, no reports, LF/CRLF recovery and literal interior U+FEFF.

### Saved-report section links

The HTML viewer now includes local links to each displayed report section.
The offline inventory example includes the same viewer and regenerated HTML.
