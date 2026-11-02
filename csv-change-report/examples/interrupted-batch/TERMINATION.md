# Optional actual Linux process termination experiment

This separate example creates trusted synthetic CSVs and ten comparisons, starts
its own process group, and sends SIGTERM after at least one pair completes while
the next pair has started. It finally sends SIGKILL to that same group and checks
Linux /proc for executing members before inspecting files. It tests termination
plus cleanup, not SIGTERM handling alone, power loss, fsync durability, atomicity,
concurrent writers, or customer data. Do not adapt it to production processes.

Requires Linux with /proc and Python 3.10+; tested on Linux Python 3.12 only.
No dependencies or network. From the extracted csv-change-report directory:

```sh
python3 examples/interrupted-batch/terminate-demo.py termination-demo
```

Choose a nonexistent output directory with an existing parent. An occupied path,
including a symlink, is refused with status 2. A successful experiment exits 0.
The batch itself returns -15, incomplete inspection commands return 2, and the
fresh comparison/index return 1 because the invented exports differ. These are
expected statuses, checked by the script. A fast/overloaded machine can miss the
bounded termination window; unexpected timing or assertions fail the experiment.
Preserve the output and investigate instead of treating failure as recovery proof.

The script creates two 10000-row CSVs (about 18 MB combined) and retains all
reports/diagnostics. Allow roughly 100 MB free and up to a few minutes. It waits
at most 50 seconds for the trigger and bounds each subsequent command at 120
seconds. Run in the foreground; do not launch it as a background service.

Inspect test-results.json and both terminated/index.html and fresh/index.html.
The stopped snapshot has completed and incomplete pairs; no automatic totals
file is assumed. The original ten-pair manifest is rerun into fresh: five equal,
five changed, no incomplete pairs. The original inputs and all stopped reports
are hash checked and preserved; the stopped output is never resumed or repaired.
Reports and diagnostics remain on disk after success or failure. Remove only
your synthetic experiment directory after reviewing it, if desired.

For the simpler simulation use [README.md](README.md). For recovery principles
see [RECOVERY.md](../../evaluation/RECOVERY.md). Browser interaction, Windows,
macOS, Python 3.10 and power loss are untested by this recipe.
