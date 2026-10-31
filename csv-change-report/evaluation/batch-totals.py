#!/usr/bin/env python3
"""Summarize a batch status table without executing it; optionally sum successful reports."""
import argparse
import json
import re
import runpy
import sys
from pathlib import Path


def validated_table(path, expected):
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
    return dict(expected=expected, completed=completed, **totals), [line.split("\t") for line in lines[1:]]


def summarize(path, expected):
    return validated_table(path, expected)[0]


def row_counts(path, totals, table_rows=None):
    """Only generated report names from an already validated table are opened."""
    rows = dict(added=0, removed=0, changed=0, unchanged=0)
    directory = Path(path).parent
    if table_rows is None:
        _, table_rows = validated_table(path, totals['expected'])
    for stem, status, _, _ in table_rows:
        if status not in ('0', '1'):
            continue
        counts = json.loads((directory / (stem + '.json')).read_text(encoding='utf-8'))['counts']
        for name in rows:
            value = counts[name]
            if type(value) is not int or value < 0:
                raise ValueError('invalid row count')
            rows[name] += value
    return dict(rows=rows, partial=bool(totals['error'] or totals['incomplete']))


def column_counts(path, totals, table_rows, aggregate=True, per_pair=False, include_rows=False):
    """Aggregate successful report counts, never opening CSV inputs."""
    reader = runpy.run_path(str(Path(__file__).with_name('column-tally.py')))
    rows = dict(added=0, removed=0, changed=0, unchanged=0)
    columns = {}
    pairs = []
    records = cells = reports = 0
    for stem, status, _, _ in table_rows:
        if status not in ('0', '1'):
            continue
        report = reader['validated_report'](Path(path).parent / (stem + '.json'))
        result = reader['tally_report'](report)
        if include_rows:
            for name in rows:
                rows[name] += report['counts'][name]
        if status == '0' and result['changed_records']:
            raise ValueError('equal status contradicts report')
        if per_pair:
            pairs.append(dict(pair=stem, **result))
        records += result['changed_records']
        cells += result['changed_cells']
        reports += 1
        for column in result['columns']:
            name = column['column']
            columns[name] = columns.get(name, 0) + column['changed_cells']
    output = dict(partial=bool(totals['error'] or totals['incomplete']))
    if include_rows:
        output['rows'] = rows
    if aggregate:
        output['column_tally'] = dict(reports=reports, changed_records=records,
            changed_cells=cells, columns=[dict(column=name, changed_cells=columns[name])
                                         for name in sorted(columns)])
    if per_pair:
        output['pair_column_tallies'] = pairs
    return output



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('table')
    parser.add_argument('--expected-pairs', type=int, required=True)
    parser.add_argument('--row-counts', action='store_true', help='sum row counts from successful pair reports; failed pairs excluded')
    parser.add_argument('--column-counts', action='store_true', help='sum changed-cell counts from successful reports; failed pairs excluded')
    parser.add_argument('--pair-column-counts', action='store_true', help='show separate changed-cell counts for each successful pair; failed pairs excluded')
    args = parser.parse_args()
    try:
        totals, table_rows = validated_table(args.table, args.expected_pairs)
        if args.column_counts or args.pair_column_counts:
            totals.update(column_counts(args.table, totals, table_rows,
                                        aggregate=args.column_counts, per_pair=args.pair_column_counts,
                                        include_rows=args.row_counts))
        elif args.row_counts:
            totals.update(row_counts(args.table, totals, table_rows))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, RecursionError):
        print('Cannot summarize: unreadable, malformed or inconsistent table/report; preserve it and inspect the run.', file=sys.stderr)
        return 2
    print(json.dumps(totals, sort_keys=True))
    return 2 if totals['error'] or totals['incomplete'] else 1 if totals['changed'] else 0


if __name__ == '__main__':
    sys.exit(main())
