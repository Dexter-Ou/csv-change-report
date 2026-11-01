#!/usr/bin/env python3
"""Create a local static HTML view of a saved CSV Change JSON report."""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 8 * 1024 * 1024


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate field')
        result[key] = value
    return result


def validate(report):
    """Check structure and internal totals, not authenticity of the source CSVs."""
    def require(condition):
        if not condition:
            raise ValueError('invalid report')

    require(type(report) is dict)
    version = report.get('format_version')
    require(type(version) is int and version in (1, 2))
    base = {'format_version', 'tool_version', 'before_sha256', 'after_sha256',
            'counts', 'changed_cells_by_column'}
    details = {'added_after_records', 'removed_before_records', 'changed_records'}
    required = base | (details if version == 1 else {'report_mode'})
    require(required <= report.keys() and not report.keys() - required - {'ignored_columns'})
    require(type(report['tool_version']) is str and bool(report['tool_version']))
    if version == 2:
        require(report['report_mode'] == 'summary')
    for name in ('before_sha256', 'after_sha256'):
        require(type(report[name]) is str and re.fullmatch('[0-9a-f]{64}', report[name]) is not None)
    c = report['counts']
    require(type(c) is dict and c.keys() == {'before', 'after', 'added', 'removed', 'changed', 'unchanged'})
    require(all(type(v) is int and 0 <= v <= 50000 for v in c.values()))
    require(c['before'] == c['removed'] + c['changed'] + c['unchanged'])
    require(c['after'] == c['added'] + c['changed'] + c['unchanged'])
    columns = report['changed_cells_by_column']
    require(type(columns) is dict)
    require(all(type(k) is str and bool(k) and type(v) is int and 0 <= v <= c['changed'] for k, v in columns.items()))
    require(sum(columns.values()) >= c['changed'])
    ignored = report.get('ignored_columns', [])
    require(type(ignored) is list and all(type(k) is str and bool(k) for k in ignored))
    require(len(set(ignored)) == len(ignored) and not set(ignored) & columns.keys())
    if version == 1:
        for field, count, bound in [('added_after_records', 'added', 'after'), ('removed_before_records', 'removed', 'before')]:
            positions = report[field]
            require(type(positions) is list and len(positions) == c[count])
            require(all(type(n) is int and 1 <= n <= c[bound] for n in positions))
            require(len(set(positions)) == len(positions))
        changes = report['changed_records']
        require(type(changes) is list and len(changes) == c['changed'])
        old, new, tally = set(), set(), Counter()
        for row in changes:
            require(type(row) is dict and row.keys() == {'before_record', 'after_record', 'columns'})
            for field, bound in [('before_record', 'before'), ('after_record', 'after')]:
                require(type(row[field]) is int and 1 <= row[field] <= c[bound])
            names = row['columns']
            require(type(names) is list and bool(names) and all(type(k) is str and k in columns for k in names))
            require(len(names) == len(set(names)))
            require(row['before_record'] not in old and row['after_record'] not in new)
            old.add(row['before_record']); new.add(row['after_record']); tally.update(names)
        require(not old & set(report['removed_before_records']))
        require(not new & set(report['added_after_records']))
        require(all(tally[k] == v for k, v in columns.items()))
    return report


def render(report):
    validate(report)
    def table(headers, rows):
        return '<table><thead><tr>' + ''.join('<th scope="col">' + escape(str(v)) + '</th>' for v in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + escape(str(v)) + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table>'
    c = report['counts']
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;">',
             '<title>Saved CSV change report</title><main><h1>Saved CSV change report</h1>',
             '<p>Local view of saved metadata. Internal totals checked; source authenticity has not been verified. No CSV cell values are included.</p>',
             '<h2>Record counts</h2>', table(['Measure', 'Records'], c.items()),
             '<h2>Changed cells by column</h2>', table(['Column', 'Changed cells'], report['changed_cells_by_column'].items())]
    if report.get('ignored_columns'):
        parts += ['<h2>Ignored columns</h2><ul>' + ''.join('<li>' + escape(n) + '</li>' for n in report['ignored_columns']) + '</ul>']
    if report['format_version'] == 2:
        parts += ['<h2>Record positions</h2><p>Summary only: record positions were omitted from this saved report. Zero details must not be inferred.</p>']
    else:
        parts += ['<h2>Record positions</h2><p>Positions are 1-based data records, excluding the header; they are not physical line numbers when fields contain newlines.</p>']
        for field, title in [('added_after_records', 'Added positions in after CSV'), ('removed_before_records', 'Removed positions in before CSV')]:
            parts += ['<h3>' + title + '</h3>', table(['Record'], ((n,) for n in report[field])) if report[field] else '<p>None</p>']
        parts += ['<h3>Changed records</h3>', table(['Before record', 'After record', 'Columns'], ((r['before_record'], r['after_record'], json.dumps(r['columns'], ensure_ascii=True)) for r in report['changed_records'])) if report['changed_records'] else '<p>None</p>']
    parts += ['<h2>Saved source hashes</h2>', table(['Input', 'SHA-256'], ((n, report[n + '_sha256']) for n in ('before', 'after'))), '<p>Tool version: ' + escape(report['tool_version']) + '</p></main></html>']
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', help='saved single-pair JSON report (not a batch manifest)')
    parser.add_argument('--output', required=True, help='new HTML file in a trusted directory; existing paths refused')
    args = parser.parse_args()
    try:
        with Path(args.report).open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('oversize report')
        report = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
        html = render(report)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
        print('E_REPORT: unreadable, unsupported or inconsistent report (8 MiB maximum); no HTML created.', file=sys.stderr)
        return 2
    try:
        with Path(args.output).open('x', encoding='utf-8') as stream:
            stream.write(html)
    except (OSError, ValueError):
        print('E_OUTPUT: cannot create new HTML; choose a fresh path in a trusted directory. A failed write may leave a partial file.', file=sys.stderr)
        return 2
    print('Created local HTML review. Open it in your browser; it contains saved report metadata.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
