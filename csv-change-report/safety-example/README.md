# Offline HTML label safety example

Fictional CSV data with markup-like column labels, quotes, ampersands and Unicode. Open `report.html` locally to inspect the saved output. The `.invalid` URLs are literal column labels, not links or resource destinations. CSV cell values are omitted from the HTML, but column names and metadata can still be sensitive with your own data.

## Regenerate

Requires Python 3.10 or newer and the CSV Change Report source. This saved example was generated with source revision `15a6465483ae34e93dc030937d5b276ad5424303`.

1. Download and extract the source archive. Locate the inner `csv-change-report` directory containing `csv_change.py` and `view_report.py`.
2. Copy this entire `safety-example` folder into that inner directory. If it is already there, skip the copy.
3. From that inner directory run:

```sh
python3 safety-example/regenerate.py
```

On systems where Python 3 is named `python`, substitute `python`; on Windows with the Python launcher, use `py -3`. The script passes labels directly as arguments, without shell quoting. It creates `new-report.json` and `new-report.html` next to this README. Existing output files are refused; move or remove only those generated files before regenerating. The included `report.json` and `report.html` are left intact. Open `new-report.html` locally.

Automated synthetic checks passed on Linux with Python 3.12.15. Static HTML parser checks verified literal label text, restrictive content security policy and absence of executable/resource elements in this example. This is not a comprehensive security audit. Interactive browser, assistive-technology, Windows/macOS and Python 3.10 execution have not been tested. Source hash matching verifies file bytes, not provenance. Use only trusted local source and output directories. The repository MIT license applies.
