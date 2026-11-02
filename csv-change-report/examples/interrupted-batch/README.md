# Try stopped-batch recovery offline

This example uses invented CSVs to create a **simulated** stopped batch, then
reruns both comparisons into a fresh directory. It does not interrupt a process
or test power loss, concurrent writers, atomicity or crash durability.

Requires Python 3.10+; no install or network. From the extracted
`csv-change-report` directory, run:

```sh
python3 examples/interrupted-batch/demo.py interrupted-batch-demo
```

The demonstration exits 0 when its expected checks pass. Its comparison/index
commands intentionally return 2 for the incomplete snapshot and 1 for the fresh
run with differences. An unexpected result stops the demonstration; preserve
its output directory and investigate. Repeating the command refuses the existing
directory; choose a new name rather than deleting an earlier attempt.

Open these two local files:

- `interrupted-batch-demo/simulated-stopped/index.html`: EQUAL followed by
  INCOMPLETE, with four Unavailable counts for pair 2.
- `interrupted-batch-demo/fresh-rerun/index.html`: EQUAL (0 / 0 / 0 / 3), then
  CHANGED (1 / 1 / 1 / 1), in added / removed / changed / unchanged order.

The script first creates a completed reference, copies its first status row and
saved files into a new simulated snapshot, and builds that snapshot's index.
It verifies hashes, checks that reusing the stopped output is refused, and reruns
the original two-pair manifest into `fresh-rerun`. The reference and stopped
snapshot remain intact. It never resumes or repairs the stopped run.

For real work, stop all writers before inspection, keep every original report
and diagnostic, and use the original intended pair count, not the surviving row
count. A partial or malformed table cannot establish why a run stopped. Run the
original manifest against retained inputs into a new output directory; resolve
invalid inputs with their data owner before changing a separate copy. Differences
still need review. Hash checks here cover ordinary trusted files at observation
time. Keep private exports and generated reports private.

For an optional experiment that terminates its own synthetic batch process group,
see [actual Linux process termination](TERMINATION.md).

See [the recovery walkthrough](../../evaluation/RECOVERY.md) and
[batch index limits](../../evaluation/BATCH-INDEX.md).
Tested on Linux only; browser interaction/accessibility and Windows/macOS untested.
