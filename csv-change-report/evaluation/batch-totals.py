#!/usr/bin/env python3
"""Summarize a batch status table without executing it or opening its reports."""
import argparse
import json
import re
import sys
from pathlib import Path


def summarize(path, expected):
    if expected < 1:
        raise ValueError('expected pairs must be positive')
    raw = Path(path).read_bytes()
    if not raw.endswith(b'\n'):
        raise ValueError('table has an unfinished line')
    lines = raw.decode('utf-8').splitlines()
    if not lines or lines[0] != 'pair\tstatus\treport\tdiagnostic':
        raise ValueError('invalid table header')
    totals = dict(equal=0, changed=0, error=0, incomplete=0)
    for index, line in enumerate(lines[1:], 1):
        fields = line.split('\t')
        stem = f'pair-{index:04d}'
        if len(fields) != 4 or fields[0] != stem:
            raise ValueError('invalid or out-of-order table row')
        _, status, report, diagnostic = fields
        if not re.fullmatch(r'0|[1-9][0-9]*', status):
            raise ValueError('invalid status')
        if diagnostic != stem + '.stderr':
            raise ValueError('invalid diagnostic name')
        expected_report = stem + '.json' if status in ('0', '1') else '-'
        if report != expected_report:
            raise ValueError('inconsistent report name')
        totals['equal' if status == '0' else 'changed' if status == '1' else 'error'] += 1
    completed = len(lines) - 1
    if completed > expected:
        raise ValueError('table exceeds expected pair count')
    totals['incomplete'] = expected - completed
    return dict(expected=expected, completed=completed, **totals)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('table')
    parser.add_argument('--expected-pairs', type=int, required=True)
    args = parser.parse_args()
    try:
        totals = summarize(args.table, args.expected_pairs)
    except (OSError, UnicodeError, ValueError):
        print('Cannot summarize: unreadable, malformed or inconsistent table; preserve it and inspect the run.', file=sys.stderr)
        return 2
    print(json.dumps(totals, sort_keys=True))
    return 2 if totals['error'] or totals['incomplete'] else 1 if totals['changed'] else 0


if __name__ == '__main__':
    sys.exit(main())
