# Troubleshoot missing or repeated CSV keys

This runnable example uses fictional records. Run it from the product folder
containing csv_change.py, with this directory at examples/stable-key/.
Python 3.10+ is required. These commands use new output filenames; the tool
refuses existing output paths. Use a fresh working directory when repeating.

A key identifies the same record across exports. Choose a stable source ID that
is populated and unique in each file. Names and row numbers usually do not make
reliable keys. Key names and values are case-sensitive; nonblank values are
compared exactly, including surrounding whitespace. All-whitespace values are
blank. Do not invent IDs simply to make an error disappear.

## 1. Diagnose a blank key

```sh
python3 csv_change.py examples/stable-key/before.csv examples/stable-key/after-blank.csv --key id --output blank-report.json
```

Expected: exit 2, stderr contains `record 2 has a blank key`, and no report is
created. Record numbers count data records, excluding the header; a quoted CSV
record can span physical lines. In this fixture, East has no ID.

## 2. Diagnose a repeated key

```sh
python3 csv_change.py examples/stable-key/before.csv examples/stable-key/after-duplicate.csv --key id --output duplicate-report.json
```

Expected: exit 2, stderr contains `record 2 repeats a key`, and no report is
created. Two records share A-101. The tool refuses an ambiguous match instead
of guessing which one to compare.

## 3. Compare corrected source records

In this fictional scenario the source system confirms that East is a new record
with ID A-104, South (A-102) was removed, and North (A-101) changed status.
after-corrected.csv represents that source correction. For real exports, verify
and repair the source or choose another stable unique key. Do not silently drop
records, overwrite duplicates, or assign IDs without source evidence. If your
export has no single stable unique column, this tool cannot safely infer one.

```sh
python3 csv_change.py examples/stable-key/before.csv examples/stable-key/after-corrected.csv --key id --output corrected-report.json
python3 view_report.py corrected-report.json --before-csv examples/stable-key/before.csv --after-csv examples/stable-key/after-corrected.csv --output corrected-report.html
python3 csv_change.py examples/stable-key/before.csv examples/stable-key/after-corrected.csv --key id --check
```

Expected: first two commands exit 0. Counts are 3 before, 3 after, 1 added
(A-104), 1 removed (A-102), 1 changed (A-101), 1 unchanged (A-103). The final
command exits 1 because differences exist; this is not an input error. The HTML
is an offline review artifact. Browser layout and accessibility are unverified.
Reports show record positions, counts and changed column names, not source key
or cell values. The IDs above describe the fixtures, not report contents.
Source-byte checks verify matching input bytes, not the truth of the records.

## Limits and recovery

Keep original exports and verify any correction with their source. The tool does not edit CSV inputs.
If a command fails, inspect stderr and retain original files; use a fresh output
name after correcting input. Never upload private exports to request help.
