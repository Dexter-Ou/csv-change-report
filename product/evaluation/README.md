# Try an offline export review

Audience hypothesis: someone who reviews recurring CSV exports by a stable unique
record key. This is a free, speculative evaluation kit for 0.1.5-preview, not
customer evidence or a paid offer. All supplied names and records are synthetic.
Python 3.10+ and a POSIX shell are required; no install, network or account needed
to run. Windows shell behavior has not been tested.

## Task (about five minutes; an estimate, not measured user timing)

Imagine approving a new export for a local workflow. Before using it, determine
whether records were added, removed or changed. Keep both snapshots intact.
From the extracted `csv-change-report` directory:

```sh
sh evaluation/review.sh examples/before.csv examples/after.csv id
sh evaluation/review.sh examples/before.csv examples/before.csv id
sh evaluation/review.sh examples/before.csv evaluation/duplicate-key.csv id
```

The first two commands should exit 0 because a comparison completed; the wrapper
handles the raw CLI's change status 1 explicitly. The third should exit 2, with a
fixed JSON diagnostic on stderr and a failure message. Do not add `set -e` around
the raw CLI without handling its expected status 1. See `EXPECTED.md` for the
answer key. Reports do not contain old/new cell values: inspect your original
snapshots locally to decide whether a change is acceptable.

For your own files, use copies in a trusted local directory, quote the paths and
provide the exact case-sensitive unique key column name:

```sh
sh evaluation/review.sh '/path/to/before.csv' '/path/to/after.csv' 'record_id'
```

The wrapper prints a text report to the terminal. Do not redirect onto an input.
It does not modify files or save reports. If it fails, preserve originals, fix a
copy of invalid input, or check Python/version/path/key, then rerun. Duplicate
keys need a domain decision; never silently discard records to make a test pass.
The main README describes input limits, exact comparisons and exclusive
`--output` behavior. For automation that needs 0=equal, 1=changed, 2=error, use
`csv_change.py --check` directly; this demonstration wrapper consumes 1.

## Optional feedback

If you choose to share feedback, open an issue at
https://github.com/Dexter-Ou/csv-change-report/issues using `FEEDBACK.md` as a prompt.
An account is needed only for GitHub feedback. Public issues are public: do not
paste private exports, cell values, column names, paths, hashes, customer details
or secrets. Describe behavior in general terms or use a tiny invented example.
No feedback is sent automatically. A lack of issues does not demonstrate success.
