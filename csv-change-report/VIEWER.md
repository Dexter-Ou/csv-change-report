# View a saved report locally

Create a static HTML review from an existing single-pair JSON report. Python 3.10+ and a browser are sufficient; no server, installation or network access is needed.

From this product directory, choose fresh output paths:

```sh
python3 csv_change.py examples/before.csv examples/after.csv --key id --output saved-review.json
python3 view_report.py saved-review.json --output saved-review.html
```

Open `saved-review.html` in a browser. It displays counts, changed cells by column, and the before/after record positions present in a detailed report. Positions count data records starting at 1, excluding the header; multiline CSV fields make these different from physical line numbers. Summary reports show that record positions were omitted. Ignored columns remain visible as a separate list.

For a large saved detailed report, explicitly omit the record-position tables:

```sh
python3 view_report.py saved-review.json --counts-only --output saved-counts.html
```

This keeps every record count, changed-cell count by column, ignored-column name and source hash. The HTML clearly labels the hidden positions; the original detailed JSON is unchanged. It still validates the entire input, including positions, and retains the 8 MiB input limit. It does not make an oversized JSON acceptable. Summary JSON remains labeled as positions omitted from the saved report, since those positions are unavailable there. The default command continues to include available positions.

The viewer checks structure and internal totals. By default it does not reopen the CSVs. It does not verify source authenticity or establish that the report came from the named tool. Batch manifests, text reports, unknown formats and reports over 8 MiB are refused. Very wide/large valid reports may exceed the viewer limit; retain the JSON and use another local inspection method.

Treat report headers and generated HTML as potentially sensitive metadata. The HTML escapes report text, contains no scripts or external resources, and requests a restrictive content security policy. It still contains column names, positions and source hashes; share only after review. Work in a trusted directory. Existing output paths are refused, including the input path. An I/O failure during a new write may leave a partial HTML file: retain your JSON and retry with a new output filename.

This preview has synthetic Linux command and HTML parser tests. Interactive browser appearance, accessibility and Windows/macOS behavior have not been tested.

Run the focused synthetic checks with:

```sh
python3 -m unittest -v test_view_report
```

Optionally compare retained CSV bytes with the hashes saved in the JSON:

```sh
python3 view_report.py saved-review.json --before-csv examples/before.csv --after-csv examples/after.csv --output saved-checked.html
```

Supply both paths explicitly; no file paths are taken from the report. This also works with `--counts-only` and summary reports. A mismatch or unreadable CSV exits 2 with `E_SOURCE` and creates no HTML. Supplying only one path is a usage error. Matching files add a clearly labeled byte-comparison result to the HTML. The files are read in chunks, without parsing CSV values; even a newline or BOM change counts as different bytes. A matching hash does not prove provenance, authenticity, or correctness of the reported differences: an edited JSON can record edited hashes. Files may change after the comparison. No source paths or values are added to the HTML. Existing outputs remain protected.

Retained CSV inputs must resolve to regular files. Directories, pipes/FIFOs, sockets and devices are refused with `E_SOURCE` before HTML creation. Symbolic links to regular files remain supported. On POSIX, the opened descriptor is checked after a nonblocking open to reject a path swapped to a FIFO. This is not a general hostile-filesystem guarantee: use trusted directories, and do not mutate inputs during comparison. Regular files may still be large or stored on slow filesystems; no runtime deadline is imposed.

Saved JSON input must also be a regular file; symlinks to regular files are
accepted. FIFOs, directories and devices are refused with `E_REPORT` before
reading. On POSIX the open is nonblocking and its descriptor is checked again,
so a path replaced by a FIFO between the checks is refused. The 8 MiB JSON
limit still applies. This is not a general runtime deadline: slow filesystems,
large regular inputs and concurrent file changes remain possible.
