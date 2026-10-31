# Answer key — synthetic, not a participant score

1. Summary JSON: --summary-only. QUICKSTART choice table and first example.
2. Default detailed JSON (omit --summary-only); retains positions and hashes,
   never old/new values. Text omits hashes. QUICKSTART choice table.
3. --check status 1. Added=1, removed=1, changed=1, unchanged=1;
   before=3, after=3. Without --check a successful comparison exits 0.
4. Pair statuses 0,1,2; aggregate 2. First two pairs produce summary JSON;
   the invalid third pair has no JSON report. Inspect status.tsv and diagnostics:
   an aggregate error neither means equality nor that every pair failed.
5. Pair statuses 2,1,0; aggregate 2. All three pairs are attempted.
   Read the evaluation kit mixed-batch instructions for sequential processing;
   QUICKSTART explicitly states error precedence, but does not itself promise
   continuation. The executable check below verifies continuation for this fixture.
6. Changed status: before_record=1, after_record=1. Record indices count parsed
   data records, excluding header, not physical file lines. Inspect originals
   locally for cell values. Preserve old outputs and choose an unused batch
   directory; the parent must exist.

Answers were checked mechanically against bundled synthetic fixtures on Linux.
