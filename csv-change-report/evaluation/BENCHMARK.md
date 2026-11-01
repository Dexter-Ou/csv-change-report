# Optional synthetic size benchmark

Run 18 comparisons of generated 50,000-record CSVs: equal, mixed and all-change,
with three repetitions each in full and summary mode. Each input has four
columns and 200,000 data cells, below the 250,000-cell and 10 MiB limits.
Quoted commas and embedded newlines are included. Only status cells change.

From the extracted product directory, on Linux with Python 3.10+:

```sh
python3 evaluation/benchmark.py './benchmark results' > benchmark-metrics.json
```

Choose a trusted local parent and a new output directory. An existing directory
is refused before fixture/report writes. The shell creates or truncates the
metrics file: choose a fresh filename and never redirect onto an input. Do not
use Python -O: assertions verify results. No installation or network is needed.
Generated inputs, JSON reports and stderr files remain in the output directory;
inspect them locally and remove that directory manually when finished. Allow
roughly 32 MiB of disk space; actual usage can vary. The benchmark process also
holds parsed reports in memory; the reported peak RSS measures each CLI child,
not the parent benchmark. A failed check exits nonzero and can leave partial
output; preserve it for diagnosis and use a new directory for another run.

It verifies expected status 0/1 with --check, exact counts and column tallies,
full-report record positions, omitted summary details, full-input hashes and
unchanged fixture bytes. JSON metrics include elapsed seconds, Linux child peak
RSS in KiB, report byte counts and hashes. All subprocesses are waited for.
Windows/macOS execution of this benchmark is unsupported.

## Observed synthetic results

Source CLI SHA-256:
`46bcbc54238384748ba649fc92ad7136b8670b15b5727073807dc4cb85be4016`

One sequential Linux/Python 3.12.15 run on 2026-11-01 used three repetitions per
scenario/mode, two available CPUs and about 7.5 GiB RAM. Input files were
1,239,913 / 1,239,913 / 1,242,023 bytes. All 18 comparisons passed.

| Scenario | Mode | Wall seconds range | Peak RSS KiB range | Report bytes |
|---|---|---:|---:|---:|
| equal | full | 0.539–0.794 | 78176–78288 | 540 |
| equal | summary | 0.555–0.586 | 78200–78308 | 482 |
| mixed | full | 0.643–0.671 | 80312–80372 | 1169347 |
| mixed | summary | 0.573–0.733 | 77440–77548 | 496 |
| all-change | full | 0.948–1.026 | 97492–97564 | 5778334 |
| all-change | summary | 0.555–0.570 | 78220–78284 | 486 |

Mixed inputs have 1,000 added, 1,000 removed, 10,000 changed and 39,000 unchanged
records, with reversed after-file order. All-change has 50,000 changed records.
Elapsed time covers child launch, comparison and report writing, excluding
fixture generation and parent verification. Linux os.wait4 provides per-child
ru_maxrss, including the interpreter. Warm-cache/order effects and other machine
load were uncontrolled. These narrow synthetic measurements are not a runtime
or memory guarantee for other data, platforms or workloads. Summary mode still
loads both inputs; smaller reports do not imply streaming. Adversarial memory,
crash and concurrent execution behavior are not established by this benchmark.
