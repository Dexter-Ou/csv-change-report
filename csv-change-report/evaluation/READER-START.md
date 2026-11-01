# Optional offline reader exercise

This source bundle includes the existing 0.1.10-preview product and
an optional six-task worksheet. No installation, network or account is needed.
Requires Python 3.10+ and a POSIX shell. Linux command checks only. All examples are synthetic.

Extract the source ZIP linked from the repository README into a new trusted
directory, then enter its inner csv-change-report folder. Read QUICKSTART.md and
evaluation/READER-TASK.md. Record answers locally before opening
evaluation/ANSWER-KEY.md. Read evaluation/README.md for batch commands and
continuation behavior. Use only the bundled invented CSVs for this exercise.

The following setup check prints the interpreter version and verifies that you
are in the right folder. It does not run comparisons or send feedback:

```sh
python3 --version
test -f csv_change.py
test -f QUICKSTART.md
test -f evaluation/READER-TASK.md
test -f evaluation/ANSWER-KEY.md
```

Then use the literal examples in QUICKSTART.md. The batch example creates
`quickstart reports`; choose a fresh extraction or unused directory before rerunning.
Status 1 with --check means changes; status 2 means an error. Preserve outputs.
The optional worksheet has no timing target or automatic score. 

Feedback is voluntary through the public issue route described in
evaluation/FEEDBACK.md. Send general observations or invented examples only;
never private CSVs, reports, paths, hashes, identifiers or secrets. Nothing is
sent automatically. See evaluation/TIMESTAMP-RECIPE.md for a worked timestamp-export example
with expected counts. The public source archive includes this reader exercise.

See [MIXED-BATCH-RECIPE.md](MIXED-BATCH-RECIPE.md) for added/removed rows, an equal pair and a failed pair with explicit partial totals.
