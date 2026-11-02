# CSV Change runnable terminal walkthrough

Unzip this bundle, then run `python3 run_tour.py` from its directory (Python 3.10+).
You can also run the script by absolute path from another directory. No package
installation, network, account or real CSV input is needed. Do not use Python -O:
the walkthrough uses assertions to verify synthetic results.

The six invented examples demonstrate detailed text/JSON, summary JSON, changed
check (status 1), equal check (status 0), and duplicate-key error (status 2).
The walkthrough itself exits 0 after all checks pass. A missing/modified source
archive exits 2 before extraction. Reports omit cell values but expose column
names, counts and positions; treat real report metadata as potentially sensitive.

Source: https://github.com/Dexter-Ou/csv-change-report/tree/6dffce2b04e7e5b88100287611773e500ae0e6d9
The bundled source archive is Base64 encoded across package.zip.b64.part* files (plain transport
encoding, not encryption). The runner decodes it and checks SHA-256 before temporary
extraction; this
checks consistency, not an independent signature. The archive includes the MIT
license. The runner reads only its adjacent package and temporary synthetic data;
it offers no user-data path argument. Temporary extraction is cleaned after the
run, including failed checks. If interrupted by a hard process kill, the OS temp
directory may retain synthetic source files; no real CSV data is used.

TERMINAL-TOUR.md is a prior recorded Linux transcript. The runnable tour prints
fresh subprocess results. These are synthetic command tests, not screenshots. Linux tested; Windows/macOS untested. Interactive browser
behavior is untested. No hosted service is required. Restore/re-extract the original
bundle if its hash check fails; the runner never overwrites the source archive.
