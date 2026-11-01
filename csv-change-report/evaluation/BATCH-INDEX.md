# Review batch results offline

After every batch writer has stopped, run from the extracted product directory:

```sh
python3 evaluation/batch-index.py '/path/to/reports' --expected-pairs 3
```

Use the original manifest pair count, never the number of saved status rows.
Open `/path/to/reports/index.html` locally. It links validated JSON summaries
and available diagnostics. It does not generate per-pair HTML comparison views.
Status 0 means equal, 1 changed, and 2 review required or creation refused. A
created page labels failed comparisons, missing/invalid summaries, missing
or unsafe diagnostics, and incomplete pairs. Malformed/truncated tables refuse
creation. Existing index files are preserved; keep the old snapshot, then move
it aside deliberately before generating another. No resume or repair occurs.

Keep exports, reports and diagnostics private. Links are fixed generated local
filenames; no scripts, external assets, CSV loading or network calls are used.
The index validates summary structure and comparator status, not source
provenance, diagnostic contents, safe concurrent writers or crash durability.
A wrong supplied pair count can hide missing work. Regular-file symlinks are
refused for linked files and the table; trusted, stopped directories are required.
Tests inspect HTML source and local links; browser interaction and accessibility
have not been verified. Use RECOVERY.md for a fresh-directory retry.

The supplied expected count must be 1–100. The status table must be at most
64 KiB; each linked summary must be at most 1 MiB. A larger otherwise valid
summary is labeled unavailable by this index; preserve it and inspect it with
the other report tools. These index limits do not change comparator limits.

## If creation is refused

An out-of-range count message means use the original manifest count (1–100),
then retry. An existing-index message means preserve the stopped directory,
then deliberately move the old index aside before regenerating. Other refusals
point to the saved status table, linked files or output permissions. Keep the
original snapshot; do not edit status rows to force acceptance. For a malformed
or interrupted run, follow RECOVERY.md and recompute into a fresh directory.
