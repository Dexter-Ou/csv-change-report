#!/usr/bin/env python3
"""Print per-column changed-cell counts from one CSV Change Report JSON file."""
import argparse
import json
from pathlib import Path
import sys

MAX_BYTES = 16 * 1024 * 1024


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate field')
        result[key] = value
    return result


def tally(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('report too large')
    report = json.loads(raw, object_pairs_hook=unique_object,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('constant')))
    if not isinstance(report, dict) or type(report.get('format_version')) is not int:
        raise ValueError('invalid report')
    version = report['format_version']
    if version not in (1, 2) or (version == 2 and report.get('report_mode') != 'summary'):
        raise ValueError('unsupported report')
    counts = report.get('counts')
    names = ('before', 'after', 'added', 'removed', 'changed', 'unchanged')
    if not isinstance(counts, dict) or any(type(counts.get(n)) is not int or counts[n] < 0 for n in names):
        raise ValueError('invalid counts')
    if (counts['before'] != counts['removed'] + counts['changed'] + counts['unchanged'] or
            counts['after'] != counts['added'] + counts['changed'] + counts['unchanged']):
        raise ValueError('inconsistent counts')
    columns = report.get('changed_cells_by_column')
    if not isinstance(columns, dict) or len(columns) > 256:
        raise ValueError('invalid columns')
    if any(not name or type(value) is not int or not 0 <= value <= counts['changed']
           for name, value in columns.items()):
        raise ValueError('invalid column count')
    if sum(columns.values()) < counts['changed']:
        raise ValueError('inconsistent column total')
    return {'format_version': 1, 'changed_records': counts['changed'],
            'changed_cells': sum(columns.values()),
            'columns': [{'column': name, 'changed_cells': columns[name]}
                        for name in sorted(columns)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report')
    args = parser.parse_args()
    try:
        result = tally(args.report)
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
        print('Cannot tally: unreadable, oversized, malformed or inconsistent report.', file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
