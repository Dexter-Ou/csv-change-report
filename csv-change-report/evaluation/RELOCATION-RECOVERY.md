# Relocate a retained automation bundle

Use this standalone synthetic exercise from the extracted product directory in a
trusted local workspace. Requires Python 3.10+ and a POSIX shell; no installation
or network. Copy the whole block once. It refuses an occupied practice directory.

Keep the manifest, exact CSV inputs, reports and diagnostics together. Here both
CSV paths are relative to the manifest directory, not the caller's working
directory. An absolute input path, or a relative path escaping the retained
bundle, is not made portable by copying the manifest. For real data, stop writers
and recover trusted copies first; never invent missing exports.

```sh
python3 - <<'PYCODE'
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

product = Path.cwd().resolve()
base = product / 'relocation practice'
if base.exists():
    raise SystemExit('Practice directory occupied; preserve it and choose a fresh path.')
base.mkdir()
def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}
original = base / 'original bundle'
(original / 'inputs').mkdir(parents=True)
for name in ('before.csv', 'after.csv'):
    shutil.copyfile(product / 'examples' / name, original / 'inputs' / name)
manifest = {'version': 1, 'pairs': [
    {'before': 'inputs/before.csv', 'after': 'inputs/after.csv', 'key': 'id'},
    {'before': 'inputs/before.csv', 'after': 'inputs/before.csv', 'key': 'id'}]}
(original / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
unrelated = base / 'unrelated cwd'
unrelated.mkdir()
def run(helper, *args):
    return subprocess.run([sys.executable, str(product / 'evaluation' / helper),
                           *map(str, args)], cwd=unrelated,
                          capture_output=True, text=True, timeout=30)
def generate(bundle, output):
    result = run('automate-batch.py', bundle / 'manifest.json', output)
    if result.returncode != 1 or json.loads(result.stdout)['code'] != 'CHANGED':
        raise SystemExit('Generation failed; preserve files and inspect: ' + result.stderr)
def totals(directory):
    result = run('batch-totals.py', directory / 'status.tsv', '--expected-pairs', 2,
                 '--row-counts', '--column-counts', '--pair-column-counts')
    if result.returncode != 1:
        raise SystemExit('Totals unavailable; preserve files and inspect: ' + result.stderr)
    value = json.loads(result.stdout)
    if value['partial'] is not False:
        raise SystemExit('Partial totals; inspect the retained reports.')
    return value

generate(original, original / 'baseline')
expected = totals(original / 'baseline')
saved = snapshot(original)
moved = base / 'relocated bundle'
shutil.copytree(original, moved)
# Make the old absolute location unavailable, retaining every original byte.
offline = base / 'original bundle offline'
original.rename(offline)
retained = snapshot(moved)
generate(moved, moved / 'regenerated')
actual = totals(moved / 'regenerated')
if actual != expected:
    raise SystemExit('Totals differ; preserve both runs and investigate.')
current = snapshot(moved)
if any(current.get(name) != digest for name, digest in retained.items()):
    raise SystemExit('Relocated retained file changed; investigate.')
occupied = run('automate-batch.py', moved / 'manifest.json', moved / 'regenerated')
if (occupied.returncode != 2 or json.loads(occupied.stdout)['code'] != 'E_OUTPUT'
        or snapshot(moved) != current or snapshot(offline) != saved):
    raise SystemExit('Unexpected occupied-output result or changed files; investigate.')
print(json.dumps({'matching_validated_totals': actual}, sort_keys=True))
print('Occupied output refused; original and relocated retained files unchanged.')
PYCODE
```

Expected: two completed comparisons, one changed and one equal, partial=false.
Validated row totals are added=1, removed=1, changed=1, unchanged=4; column totals
cover two reports with changed_records=1 and changed_cells=1. Per-pair column
totals also match the baseline. Status 1 means differences requiring review.

The block copies a self-contained bundle to a path containing spaces, renames the
original directory within the practice workspace, and runs from an unrelated
working directory using absolute helper paths. The old original path is absent;
its bytes remain under `original bundle offline`. The relocated baseline and
inputs remain intact. Regeneration uses a new directory. An occupied-output
control expects status 2 / E_OUTPUT and unchanged files. Repeating the whole
block refuses before changing practice files; choose a new practice name rather
than deleting evidence to reuse it.

Matching totals do not prove byte-for-byte report identity or prove the retained
inputs match lost originals. This tests synthetic ordinary files on Linux, not
crash durability, concurrent edits, hostile paths or cross-platform behavior.
Copies within one VM are local snapshots, not off-VM backups. Keep private CSVs
and diagnostics private; this guide does not upload data.
