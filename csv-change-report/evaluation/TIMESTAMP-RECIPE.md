# Worked example: ignore export timestamps

Run from the folder containing csv_change.py. Requires Python 3.10+ and a
POSIX shell; no installation or network. All records below are invented.
Choose a fresh extraction: the block creates `timestamp demo` and stops if it
already exists. Preserve reports; remove only your own demo directory to reset.

```sh
mkdir 'timestamp demo'
cat > 'timestamp demo/before.csv' <<'CSV'
id,status,updated
A,open,2026-10-30
B,open,2026-10-30
C,closed,2026-10-30
CSV
cat > 'timestamp demo/after.csv' <<'CSV'
id,status,updated
A,open,2026-10-31
B,closed,2026-10-31
D,open,2026-10-31
CSV
python3 csv_change.py 'timestamp demo/before.csv' 'timestamp demo/after.csv' --key id --format json --output 'timestamp demo/baseline.json'
python3 csv_change.py 'timestamp demo/before.csv' 'timestamp demo/after.csv' --key id --ignore-column updated --format json --output 'timestamp demo/filtered.json'
python3 - <<'PYTHON'
import json
for name in ('baseline', 'filtered'):
    with open('timestamp demo/' + name + '.json', encoding='utf-8') as stream:
        report = json.load(stream)
    print(name + ':', json.dumps(report['counts'], sort_keys=True))
PYTHON
```

Expected output (JSON key order shown by the printing command):

```text
baseline: {"added": 1, "after": 3, "before": 3, "changed": 2, "removed": 1, "unchanged": 0}
filtered: {"added": 1, "after": 3, "before": 3, "changed": 1, "removed": 1, "unchanged": 1}
```

A becomes unchanged when `updated` is ignored. B still changes because its status
changes. C is removed and D is added in both reports. Reports identify changed
columns and record locations, and omit cell values. Ignoring a column does not
hide added/removed keys or relax key uniqueness. You cannot ignore the key.

The commands omit `--check`, so successful report creation exits 0 even when
records differ. Add `--check` in automation when you want exit 1 for differences;
exit 2 means an input/usage error. Ignore only fields you deliberately consider
irrelevant: meaningful changes in an ignored field will also be suppressed.
Timestamp parsing, normalization and automatic volatile-field detection are not
performed. Linux synthetic command verification is not independent user feedback.
