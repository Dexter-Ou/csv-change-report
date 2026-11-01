# Preview a CSV review

Inspect these invented examples here, then [run the quick start](QUICKSTART.md)
with Python 3.10+. This free MIT-licensed preview runs locally without an account,
installation or network connection. Examples are synthetic.

## One changed export

Compare [before.csv](examples/before.csv) and [after.csv](examples/after.csv),
using `id` as the unique record key. The [saved detailed JSON](examples/expected-report.json)
records these results:

| Before rows | After rows | Added | Removed | Changed | Unchanged |
| --- | --- | --- | --- | --- | --- |
| 3 | 3 | 1 | 1 | 1 | 1 |

The changed record is data record 1 in each snapshot, in column `status`.
The added record is after record 2; the removed record is before record 2.
Positions exclude the header and count parsed records, not physical lines.
Reports omit key and cell values: inspect the original snapshots to see values.
[Create a local HTML view](VIEWER.md) to review counts and positions in a browser.

## Several pairs in one index

The [mixed-batch walkthrough](examples/mixed-batch/README.md) compares three
pairs in manifest order and creates a local HTML index:

| Pair | Label | Added | Removed | Changed | Unchanged |
| --- | --- | --- | --- | --- | --- |
| 1 | EQUAL | 0 | 0 | 0 | 3 |
| 2 | CHANGED | 1 | 1 | 1 | 1 |
| 3 | ERROR — comparison failed | Unavailable | Unavailable | Unavailable | Unavailable |

Pair 3 deliberately repeats a key. Both batch and index commands return 2;
Unavailable means missing counts, never zero. Follow saved summary and diagnostic
links after all writers stop. The index links JSON summaries and diagnostics,
not per-pair HTML views. Changed counts refer to records, not changed cells.

## Keep stopped work and start fresh

The [simulated stopped-batch walkthrough](examples/interrupted-batch/README.md)
preserves one finished pair plus one unfinished pair. Its stopped index shows
EQUAL then INCOMPLETE, with four Unavailable counts for the unfinished pair.
Rerunning the original manifest into a new directory yields EQUAL then CHANGED.
This demonstration simulates a stopped snapshot; it does not interrupt, resume
or repair a process. Keep original inputs, outputs and diagnostics together.

## Before using private exports

Use comma-separated UTF-8, matching column sets and one nonblank unique key per
record. Keep inputs and reports private: column names, counts, hashes and record
positions can be sensitive. Work in trusted local directories with writers
stopped. Existing output destinations are refused; failed writes may leave
partial new files. Preserve them and choose fresh paths for retries.

Read [full comparison limits](README.md), [index limits](evaluation/BATCH-INDEX.md)
and [recovery guidance](evaluation/RECOVERY.md). Index limits include 1–100 expected
pairs, a 64 KiB status table and 1 MiB per summary. A report is not export approval
or proof of source authenticity. Synthetic Linux command checks cover these
examples; interactive browser appearance, accessibility and Windows/macOS are untested.
