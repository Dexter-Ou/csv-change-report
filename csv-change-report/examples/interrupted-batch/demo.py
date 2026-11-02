#!/usr/bin/env python3
"""Synthetic stopped-batch demonstration; run from the product directory."""
import hashlib
import shutil
from pathlib import Path
import subprocess
import sys


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def invoke(args, expected):
    result = subprocess.run([sys.executable, *map(str, args)], capture_output=True)
    if result.returncode != expected:
        raise RuntimeError('Unexpected command status; preserve all files and investigate.')
    return result


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 examples/interrupted-batch/demo.py NEW_DIRECTORY')
    root = Path.cwd()
    example = Path(__file__).resolve().parent
    if not (root / 'evaluation' / 'automate-batch.py').is_file():
        raise SystemExit('Run from the extracted csv-change-report directory.')
    base = Path(sys.argv[1])
    # Exclusive creation preserves previous runs; no cleanup or resume is attempted.
    try:
        base.mkdir()
    except FileExistsError:
        print('Output path already exists; choose a new directory. Existing files were preserved.',
              file=sys.stderr)
        return 2
    manifest = example / 'manifest.json'
    source = base / 'completed-reference'
    stopped = base / 'simulated-stopped'
    fresh = base / 'fresh-rerun'
    invoke(['evaluation/automate-batch.py', manifest, source], 1)
    stopped.mkdir()
    lines = (source / 'status.tsv').read_bytes().splitlines(keepends=True)
    (stopped / 'status.tsv').write_bytes(b''.join(lines[:2]))
    for suffix in ('json', 'stdout', 'stderr'):
        shutil.copyfile(source / ('pair-0001.' + suffix),
                        stopped / ('pair-0001.' + suffix))
    saved = snapshot(stopped)
    reference = snapshot(source)
    invoke(['evaluation/batch-index.py', stopped, '--expected-pairs', '2'], 2)
    assert {n: snapshot(stopped)[n] for n in saved} == saved
    indexed = snapshot(stopped)
    invoke(['evaluation/automate-batch.py', manifest, stopped], 2)
    assert snapshot(stopped) == indexed
    invoke(['evaluation/automate-batch.py', manifest, fresh], 1)
    invoke(['evaluation/batch-index.py', fresh, '--expected-pairs', '2'], 1)
    assert snapshot(stopped) == indexed and snapshot(source) == reference
    print('Synthetic stopped index: EQUAL, INCOMPLETE; status 2.')
    print('Occupied stopped output refused; saved files unchanged.')
    print('Fresh rerun index: EQUAL, CHANGED; status 1; differences need review.')
    print('Open ' + str(stopped / 'index.html') + ' and ' + str(fresh / 'index.html'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
