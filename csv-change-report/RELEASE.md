# 0.1.7-preview

Adds repeatable --ignore-column NAME for exact non-key column exclusions.
Reports explicitly list active exclusions; --check evaluates only retained
fields while additions/removals still count. Unknown/key columns fail closed;
full schemas, input validation, limits and full-byte hashes remain enforced.
No exclusions keeps the previous report structure, apart from tool_version.

Thirty-six synthetic acceptance methods cover comparison, errors, bounded
inputs, output handling, stdout faults and explicit column exclusions.
Run python3 -m unittest -v and the included evaluation/review.sh example.
The cycle also retains a pre-version-bump exact default-output comparison and
an independent seeded oracle; these are internal tests, not customer evidence.
No Windows/macOS, hostile-directory or crash-durability assurance.
No dependencies, network, telemetry, hosted service or paid obligation added.
