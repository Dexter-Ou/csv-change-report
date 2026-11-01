# Output failures and recovery

Run the synthetic regression from any working directory using Python 3 on Linux as a normal non-root user:

```sh
python3 /path/to/csv-change-report/evaluation/test-output-failure.py
```

No dependencies, sudo, network or real input data are needed. Do not use Python `-O`; assertions are required. Other operating systems are untested. The script retains a temporary directory, prints its path, and writes results.json plus samples.zip there. Remove only that test directory when finished. Permission-denied fixtures are mode 0555, so restore their write permission before cleanup if necessary.

The regression checks full and summary reports against unwritable parents, existing files/directories and input/output collisions. Existing bytes must survive. It then confirms a valid wide-schema comparison exceeds the 2,048-byte fault limit before applying a per-child Linux file-size limit to a two-pair batch. The first pair must return the exact write diagnostic, leave a 2,048-byte partial file, and have no report link in status.tsv. The second equal pair must still complete with a readable report. Batch, totals and index must report error exit 2.

## Recovering a failed report

An output error returns exit 2 with a diagnostic such as `output file could not be written`. A report file can remain partially written: output creation is not atomic. Do not parse, share or treat that file as a completed comparison, even when it contains readable JSON. Batch status marks the pair as ERROR and excludes the failed report from its links; a later pair may still succeed. Check status.tsv and each pair's stderr rather than assuming every file in the report directory is valid.

Preserve your original CSVs and the error/status files. Check the destination's permissions and available storage or file-size limits. Choose a fresh writable output path or a fresh batch report directory, then rerun the original comparison after resolving the cause. Existing destinations are rejected; move aside the failed artifact for diagnosis or remove only the known failed report after reviewing it. Never remove an input file or unrelated existing directory to make a retry work. Confirm the rerun's exit status and report counts before using its results. This test does not establish crash durability, race safety or cross-platform behavior.
