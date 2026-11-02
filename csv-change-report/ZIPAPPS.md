# Carry the comparator and viewer as single files

Build two Python archives from this directory using the standard library:

```sh
python3 build_zipapps.py portable-tools
```

The parent must exist and `portable-tools` must be a new directory. It contains
`csv_change.pyz` and `view_report.pyz`. Each includes its original program source
and MIT license. Copy either archive to another trusted directory; it needs no
adjacent source files, extraction, install, account or network. Python 3.10+ must
already be installed. These are Python archives, not native executables.

From the same source directory, with your original snapshots retained separately,
use the archives inside `portable-tools/`:

```sh
python3 portable-tools/csv_change.pyz before.csv after.csv --key id --check --output review.json
python3 portable-tools/view_report.pyz review.json --output review.html --before-csv before.csv --after-csv after.csv
```

Handle the comparator's status before running the viewer: `--check` returns
0 for equal, 1 for changed, and 2 for error. An error must stop the workflow.
The viewer returns 0 on successful creation and 2 for error. Open the HTML in
your local browser after successful creation. All original input, report-size,
metadata-disclosure and filesystem limits still apply; see README.md and
VIEWER.md. Output writes require hard links. Existing report/HTML destinations
are refused; cleanup failures can leave complete files with status 2. Preserve
failed-run evidence rather than deleting or retrying the same path blindly.

The build also refuses any existing destination directory. A failed build can
leave a partial directory: preserve it for inspection and select a fresh path.
Use a trusted parent without concurrent writers. Deterministic archive metadata
allows byte-for-byte repeat builds from identical sources; this is not a signed
release or proof of authenticity. Keep the source revision and verify hashes
when transferring files. Neither archive contains examples or the full guides.

Linux synthetic acceptance checks cover independent-directory execution,
comparison statuses and saved-report viewing. Windows/macOS, Python 3.10 and
interactive browser behavior remain untested.
