# CSV Change Report — tested preview

Compare two UTF-8 CSV exports by one stable unique key and produce a JSON or text change
summary. For an operator reviewing recurring exports who wants to locate changed
records without uploading their data. Free, MIT-licensed preview from Gong LLC.

**Synthetic runtime checks passed** on the isolated worker (Python 3.12.15,
2026-10-31): the included test suite, fresh extraction, example oracle and help.
This is a preview, not a hardened parser.
Requires Python 3.10+; standard library only, no installation or service.

Start with [the short report-choice guide](QUICKSTART.md) for a local review.

From this directory on the isolated worker:

```sh
python3 csv_change.py --version
python3 -m unittest -v
python3 csv_change.py examples/before.csv examples/after.csv --key id
```

The example should report 3 records before and after, one addition, one removal,
one changed record and one unchanged record. Changed column: status. These synthetic results were observed in the worker fresh-start test. The complete hand-derived
oracle is `examples/expected-report.json`; the fixture test compares against it. Record numbers exclude
the header and count parsed records rather than physical lines.

Rules: comma delimiter; exact case-sensitive column names and cell comparisons;
no trimming or type inference. Header order can change. Header column sets must
match. Blank or duplicate keys, duplicate/blank headers, wrong-width records,
invalid UTF-8, malformed quoting and NUL bytes fail closed. A changed key appears
as one removal and one addition; it is not inferred to be the same entity.
Header-only exports are valid. Limits per input: 10 MiB, 50,000 records, 256 columns and 250,000 data
cells (records times columns). Header-only files also obey the column limit; parser
field-size defaults also apply. A synthetic Linux worker test observed a default
maximum of 131072 decoded characters per field (not UTF-8 bytes): a quoted ASCII
or accented field at that boundary was accepted, and one character above it
returned status 2. The default belongs to the Python runtime; this tool does not
raise it. Increasing `--max-input-bytes` does not raise the field limit. Both snapshots and the report are held in memory;
these limits reduce object amplification but are not a benchmark or an adversarial
resource guarantee. Output lists follow source record order; changed column lists
follow the before-header order. Identical input bytes produce identical JSON
under the same Python/parser configuration. No timestamps or random IDs are added.

JSON remains the default; use `--format json` explicitly or add `--format text`
for a terminal summary of counts, added/removed record positions, changed record
positions and per-column change counts. Text omits input hashes. Column names
are JSON-quoted with Unicode and control characters escaped for terminal safety.
Both formats omit cell values and paths; errors remain fixed JSON on stderr.
For example:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --format text
```

Save a report without shell redirection by adding `--output report.json` (or
`--format text --output report.txt`). Success writes the report and leaves stdout
empty. The destination must be new: existing files, directories, hard links and
symlinks are refused. Paths resolving to either input are rejected. New files use
owner-only permissions on Linux (subject to a more restrictive process umask).
Inputs are validated before creating the output. Errors remain fixed JSON on stderr.
A write failure can leave a partial new report: inspect/remove that report yourself,
then retry with a new name. No atomic completion or crash durability is promised;
use a trusted output directory, not one concurrently modified by another process.

The JSON report includes input SHA-256, column names and record positions, but no cell
values or file paths. Column names and counts can themselves be sensitive: review
before sharing. Hashes support reproducibility, not anonymization. Inputs are
opened read-only. No network, telemetry, formula evaluation, automatic cleaning
or spreadsheet export. Do not redirect output onto either input path: shell
redirection can truncate it before this program starts. Invalid command arguments produce a fixed message without echoing supplied text;
long option abbreviations are rejected. `--help` prints usage and exits 0. `--version` prints
`csv-change-report 0.1.10-preview` and exits 0 without input files. Include this
version when voluntarily reporting a problem; do not include private CSV data.
Failures exit 2 with JSON
on stderr. By default successful comparisons exit 0, including when changes exist.
With `--check`, a completed comparison exits 1 for added, removed or changed
records and 0 otherwise. Row/header order, BOM and line-ending differences alone
do not count as content changes. Reports are still produced in either format;
`--output` must finish successfully before status 0 or 1 is returned. Errors,
including output failures, take precedence and exit 2. A full-looking output file
after exit 2 must not be treated as a completed report.

For a local review script (POSIX shell), handle each status explicitly:

```sh
status=0
python3 csv_change.py before.csv after.csv --key id --check --format text || status=$?
case "$status" in
  0) echo "No keyed content changes" ;;
  1) echo "Content changed; review the report" ;;
  *) echo "Comparison failed" >&2; exit "$status" ;;
esac
```

Use these exit statuses when scripting local comparisons.

Recovery: preserve original snapshots, source version and hashes; correct invalid
inputs in copies, then rerun. No database, persistent service or migration.

Original source by Gong LLC.
MIT licensed; see `LICENSE`. The exact archive inventory and worker
release checks are in `RELEASE-FILES.json` and `RELEASE.md`. Public source is intended for GitHub download; a repository is not a hosted site.
Local copies are not off-VM backups. Keep your own verified source copy.

Stdout is flushed before reporting completion. A broken pipe or detected stdout
write/flush failure returns 2 with a fixed JSON diagnostic. Bytes may already have
reached the consumer; treat the report as incomplete on failure. This does not
prove that a downstream program saved or accepted the report.


Ignore explicitly selected volatile fields with repeated `--ignore-column NAME`:

```sh
python3 csv_change.py before.csv after.csv --key id --check --ignore-column updated_at --ignore-column export_nonce
```

Use ignored columns to filter selected export metadata.
Names are exact and case-sensitive; duplicate selections are deduplicated. Key
columns and missing names are rejected. Both full column sets must still match.
Every input cell and row remains subject to validation/limits, and hashes cover
original full input bytes. Only selected non-key value differences are excluded;
added and removed keys still count even if every non-key column is ignored.

When exclusions are active, JSON adds `ignored_columns` in before-header order;
text lists escaped ignored names. Per-column counts omit those columns. `--check`
uses the filtered result: status 0 means no changes among compared fields, not
complete export equality. Without exclusions, report structure/content remains
unchanged except the tool version. Reports do not expose ignored cell contents.
For an included example, add `--ignore-column status` to the example command:
the changed count becomes 0, unchanged becomes 2, and added/removed stay 1 each.


For large diffs, add `--summary-only` with either JSON or text:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --summary-only
```

Counts, per-column totals, exclusions and `--check` statuses match detailed mode.
Summary JSON uses `format_version: 2` and `report_mode: "summary"`, omitting
`added_after_records`, `removed_before_records` and `changed_records` entirely.
It retains full-input SHA-256 hashes. Summary text omits record details and, like
all text output, input hashes. Default detailed JSON remains format version 1.
This is an output-size feature, not streaming: both input snapshots remain in
memory. Column names, counts and hashes can still disclose sensitive metadata.



### Smaller input byte budgets

The default per-input ceiling remains 10 MiB (10485760 bytes). Use
`--max-input-bytes N` to choose a smaller positive integer budget; values above
the fixed ceiling are refused. For example:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --max-input-bytes 4096
```

The same limit applies separately to each input, including its header, UTF-8 BOM,
line endings and all encoded bytes. An input exactly at the limit is accepted if
otherwise valid; one byte over is refused with status 2 before any report is
created. Only up to N+1 raw bytes are read per input. The limit is not a bound on
total process memory: parsed objects, decoded text and reports also consume memory.
Row, column, data-cell and CSV parser field limits still apply. The batch helper accepts the same option in first position; see
[evaluation instructions](evaluation/README.md#optional-batch-input-budget). Existing
report paths and both original inputs remain protected by the usual refusal rules.


Repeat offline batches with the optional [JSON manifest helper](evaluation/README.md#optional-repeat-review-manifest-prototype).
Use `examples/batch.json` for a synthetic changed/equal batch.

## Saved report viewer

Create a local static HTML view of a saved single-pair JSON report with `python3 view_report.py saved-review.json --output saved-review.html`. See [the viewer guide](VIEWER.md) for fresh-start commands, supported formats and limits.

CSV inputs must be regular files; symlinks to regular files are accepted.
Directories, devices and FIFOs are rejected. On POSIX, a nonblocking open and
file-descriptor check also reject a FIFO substituted after the path check.
This is not a general runtime deadline or a guarantee against all filesystem races.
