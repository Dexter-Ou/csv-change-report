# Draft release procedure

Status: 0.1.3-preview tested preview. Twenty-two synthetic test methods and the
fresh-start example/help passed on the isolated worker on 2026-10-31.
No independent customer testing or demand evidence. All fixture data is synthetic.

This tool and its included documentation are available under the MIT license
in LICENSE. It includes no external libraries or assets. Python itself is an
external runtime and is not included. Commercial use is permitted; this draft
has no paid service, customer agreement or demonstrated willingness to pay.

The complete archive inventory is RELEASE-FILES.json. Include exactly those
regular files, rooted under csv-change-report/. Reject symlinks, extra files,
absolute paths, duplicate names and parent traversal. Do not include private
exports, repository metadata, bytecode, local reports or workspace evidence.
Use a fresh directory when extracting; preserve original input snapshots.

Before describing a release as usable, extract the exact candidate archive to
a fresh directory on the approved isolated worker and run from its root:

```sh
python3 --version
python3 csv_change.py --version
python3 -m unittest -v
python3 csv_change.py examples/before.csv examples/after.csv --key id > actual-report.json
python3 -c 'import json; from pathlib import Path; assert json.loads(Path("actual-report.json").read_text()) == json.loads(Path("examples/expected-report.json").read_text())'
python3 csv_change.py --help
```

Require Python 3.10+, all twenty-two synthetic test methods passing, the fixture
comparison passing and help exiting 0. Ten subprocess methods cover the real entry point from an unrelated working
directory, fixture output, deterministic bytes, unchanged inputs, version, help, missing
files, invalid UTF-8, duplicate keys and argument errors. These passed on the approved worker. The suite covers missing input and
argument errors; confirm their exit code 2 and fixed JSON diagnostics from the
CLI as part of fresh-start verification. Record actual command results and the
archive SHA-256. Test only synthetic inputs. Any source or fixture change
requires rebuilding the archive and repeating the relevant worker checks.

Publication requires these results for the exact candidate. Immediately before an authorized
external write, persist a unique action intent; save provider outcome/receipt
before marking it complete. Inspect provider state after interruption before
resending. Preserve exact published bytes and any returned file blob SHAs.
A repository URL proves neither a hosted site nor customer use. A local ZIP
is not an off-VM backup. Record offsite verification separately.

Recovery: keep original inputs and a verified copy of the exact source/archive.
No migrations, service or installation is required. Re-extract a known revision
and rerun on input copies; never redirect a report onto an input. If verification
fails, retain the draft label and diagnose before publication.
