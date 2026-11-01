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

## Report size and memory

Use comparison `--summary` when you need aggregate counts without per-record
positions. Use viewer `--counts-only` when a detailed JSON report already exists
and you want smaller HTML. Both options omit positions from their output, but
they do different work: comparison still loads both CSV snapshots, and the
viewer still reads and validates the whole JSON, including its positions.
Neither option is a streaming mode or a fixed memory bound.

One synthetic Linux run per configuration on Python 3.12.15 measured:

| Input / operation | Default peak RSS (KiB) | With option (KiB) |
|---|---:|---:|
| Compare 50,000 rows × 5 columns per CSV | 91,972 | 62,204 (`--summary`) |
| Compare 9,998,897 bytes per CSV | 95,216 | 95,260 (`--summary`) |
| View the first detailed report (7,678,349-byte JSON) | 68,388 | 58,120 (`--counts-only`) |

Each CSV row changed in every non-key column. The first fixture reached 250,000
cells per input; the byte-heavy fixture had 999 rows × 5 columns with
2,500-character non-key fields. Summary JSON was 501 versus 7,678,349 bytes for
the first fixture, while counts-only HTML was 1,671 versus 5,479,712 bytes.
These size reductions do not imply comparable parsing-memory reductions.

RSS includes the interpreter and was measured with Linux `wait4`. Each command
ran under a test-only 512 MiB address-space ceiling, 30 CPU seconds and 45 wall
seconds; those ceilings are not imposed by the product. Cache state and machine
load were uncontrolled, and these ASCII fixtures do not cover all Unicode or
object-allocation patterns. The 44 KiB difference in the byte-heavy comparison
is too small to interpret from one sample. These observations are not an upper
bound or a cross-platform result. Keep the input limits and available memory
in mind even when choosing smaller output.
