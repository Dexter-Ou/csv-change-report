# CSV Change Report — tested preview

Compare two UTF-8 CSV exports by one stable unique key and produce a JSON or text change
summary. For an operator reviewing recurring exports who wants to locate changed
records without uploading their data. This usefulness hypothesis is unverified.
No customer testing, price, willingness to pay or earnings is established.

**Synthetic runtime checks passed** on the isolated worker (Python 3.12.15,
2026-10-31): twenty-two test methods, fresh extraction, example oracle and help.
No independent user testing has occurred. This is a preview, not a hardened parser.
Requires Python 3.10+; standard library only, no installation or service.

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
field-size defaults also apply. Both snapshots and the report are held in memory;
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

The JSON report includes input SHA-256, column names and record positions, but no cell
values or file paths. Column names and counts can themselves be sensitive: review
before sharing. Hashes support reproducibility, not anonymization. Inputs are
opened read-only. No network, telemetry, formula evaluation, automatic cleaning
or spreadsheet export. Do not redirect output onto either input path: shell
redirection can truncate it before this program starts. Invalid command arguments produce a fixed message without echoing supplied text;
long option abbreviations are rejected. `--help` prints usage and exits 0. `--version` prints
`csv-change-report 0.1.3-preview` and exits 0 without input files. Include this
version when voluntarily reporting a problem; do not include private CSV data.
Failures exit 2 with JSON
on stderr; successful comparisons exit 0, including when changes exist.

Recovery: preserve original snapshots, source version and hashes; correct invalid
inputs in copies, then rerun. No database, persistent service or migration.

Original source by the Gong LLC economic experiment; no downloaded code/assets.
MIT licensed; see `LICENSE`. The exact archive inventory and worker
release checks are in `RELEASE-FILES.json` and `RELEASE.md`. Public source is intended for GitHub download; a repository is not a hosted site.
Local copies are not off-VM backups. Keep your own verified source copy.
