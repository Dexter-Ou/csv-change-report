#!/usr/bin/env python3
"""Validate the batch comparator's version 2 summary and check exit status."""
import json
import re
import sys
from pathlib import Path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def validate_summary(path, status):
    """Check shape/internal consistency, not CSV provenance or concurrent edits."""
    report = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    required = {'format_version', 'tool_version', 'report_mode', 'before_sha256',
                'after_sha256', 'counts', 'changed_cells_by_column'}
    if type(report) is not dict or not required <= report.keys() or report.keys() - required - {'ignored_columns'}:
        raise ValueError('invalid summary fields')
    if type(report['format_version']) is not int or report['format_version'] != 2 or report['report_mode'] != 'summary':
        raise ValueError('unsupported summary format')
    if type(report['tool_version']) is not str or not report['tool_version']:
        raise ValueError('missing tool version')
    for field in ('before_sha256', 'after_sha256'):
        if type(report[field]) is not str or not re.fullmatch('[0-9a-f]{64}', report[field]):
            raise ValueError('invalid source hash')
    counts = report['counts']
    names = {'before', 'after', 'added', 'removed', 'changed', 'unchanged'}
    if type(counts) is not dict or counts.keys() != names or any(type(v) is not int or v < 0 for v in counts.values()):
        raise ValueError('invalid row counts')
    common = counts['changed'] + counts['unchanged']
    if counts['before'] != common + counts['removed'] or counts['after'] != common + counts['added']:
        raise ValueError('inconsistent row counts')
    columns = report['changed_cells_by_column']
    if type(columns) is not dict or any(type(k) is not str or not k or type(v) is not int or not 0 <= v <= counts['changed'] for k, v in columns.items()):
        raise ValueError('invalid column counts')
    if sum(columns.values()) < counts['changed']:
        raise ValueError('missing changed cells')
    ignored = report.get('ignored_columns', [])
    if type(ignored) is not list or any(type(k) is not str or not k for k in ignored) or len(set(ignored)) != len(ignored) or set(ignored) & columns.keys():
        raise ValueError('invalid ignored columns')
    expected = int(any(counts[n] for n in ('added', 'removed', 'changed')))
    if status not in ('0', '1') or int(status) != expected:
        raise ValueError('inconsistent comparator status')
    return report


def main():
    try:
        if len(sys.argv) != 3:
            raise ValueError('expected report and status')
        validate_summary(sys.argv[1], sys.argv[2])
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
        print('Invalid or inconsistent summary report; comparison is incomplete.', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
