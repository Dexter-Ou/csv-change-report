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

The viewer checks structure and internal totals. It does not reopen the CSVs, verify source authenticity, or establish that the report came from the named tool. Saved hashes support a separate comparison against retained inputs. Batch manifests, text reports, unknown formats and reports over 8 MiB are refused. Very wide/large valid reports may exceed the viewer limit; retain the JSON and use another local inspection method.

Treat report headers and generated HTML as potentially sensitive metadata. The HTML escapes report text, contains no scripts or external resources, and requests a restrictive content security policy. It still contains column names, positions and source hashes; share only after review. Work in a trusted directory. Existing output paths are refused, including the input path. An I/O failure during a new write may leave a partial HTML file: retain your JSON and retry with a new output filename.

This preview has synthetic Linux command and HTML parser tests. Interactive browser appearance, accessibility and Windows/macOS behavior have not been tested.

Run the focused synthetic checks with:

```sh
python3 -m unittest -v test_view_report
```
