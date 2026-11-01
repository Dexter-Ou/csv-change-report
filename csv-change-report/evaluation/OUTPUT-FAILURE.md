# Output failures and recovery

Run these synthetic regressions with Python 3 on Linux as a normal non-root user,
from any working directory. No dependencies, network or real input data are needed:

```sh
python3 /path/to/csv-change-report/evaluation/test-output-failure.py
python3 /path/to/csv-change-report/evaluation/test-cleanup-state.py
```

Run without `-O`. Each script prints a retained temporary directory with results
and sample artifacts. Remove only that test directory after review; the permission
fixture uses mode 0555 and may need its write permission restored for cleanup.
The first regression uses a real 2,048-byte per-child file-size limit. The second
injects unlink denial, unsupported hard links and a destination collision; these
are synthetic Linux behavior, not evidence of Windows/macOS compatibility.

## Output protocol

Reports are written to a private mode-0600 `.csv-change-` temporary sibling,
closed, then hard-linked to the requested destination without replacing it.
A pre-link write failure returns 2 and normally leaves no destination or temporary
sibling. Existing files, directories and dangling symlinks are refused.
Hard links must be supported by the destination filesystem; unsupported links
fail closed. Standard-output reporting is unchanged.

If linking succeeds but temporary unlink fails, the destination contains a complete
report, but status remains 2. A JSON stderr line reports `output_committed: true`
and `cleanup_required: true`. If unlink also fails after a write/link error,
`output_committed: false` precedes a second JSON line preserving the primary error.
Consumers must handle multiple diagnostic lines. No diagnostic contains input
values, supplied paths or OS exception text.

## Manual recovery, including batches

Preserve original CSVs, stderr and status files. Inspect permissions, storage and
file-size limits. For cleanup-required errors, verify the requested report and
inspect its directory for temporary siblings. Remove only files confirmed to
belong to that run; never glob-delete temporary files shared with other runs.
Do not delete the report blindly or retry the same output path: existing paths
are refused. If rerunning after repair, use a fresh output path or batch directory.

A batch treats every comparator status 2 as ERROR, excludes its report link and
omits it from successful totals, even if cleanup failed after a complete report
was created. Later pairs still run. Read each pair's stderr and status.tsv;
a readable JSON file alone does not establish a successful batch comparison.
Keep failed-run evidence separate from any verified rerun.

"Committed" means the link operation returned, not durable storage. There is no
fsync/power-loss guarantee. Crashes can leave temporary siblings. Adversarial
parent-directory replacement, concurrent mutation and other platforms are untested.
Use trusted input and output directories.
