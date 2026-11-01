# Malformed-input regression

From the extracted csv-change-report directory, run:

```sh
python3 evaluation/test-malformed-input.py
```

Python 3, standard library only. The script locates the product relative to itself,
so an absolute script path also works from another directory. Do not use `-O`.
Expected exit: 0. The final JSON prints `results_path`, a fresh temporary directory
containing fixtures, stdout/stderr for every command, reports and results.json.
It is retained for inspection; delete that printed directory when finished.

The synthetic checks cover duplicate keys, duplicate headers, invalid UTF-8,
short rows and long rows on either input, in full and summary-only modes.
Each must return diagnostic exit 2 without stdout or an output report.
A mixed batch must record five errors and one equal pair, with diagnostic totals
and index exit 2; duplicate manifest fields must fail before report creation.
Reader inventory hashes are checked before and after execution.
Expected diagnostic strings are stored in malformed-input/oracle.json.

Failure exits nonzero and preserves the temporary directory for inspection.
A deliberate wrong diagnostic in a disposable copy must cause a diagnostic
mismatch assertion (refresh that copy's inventory hash to reach the assertion).
These tests do not establish browser, cross-platform, race or crash durability.
