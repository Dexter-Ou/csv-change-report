#!/usr/bin/env python3
"""Create a local static HTML view of a saved CSV Change JSON report."""
import argparse
import hashlib
from collections import Counter
from html import escape
import json
import os
import stat
import tempfile
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


def read_report_bytes(path):
    """Read bounded regular-file JSON bytes, accepting regular-file symlinks."""
    if not stat.S_ISREG(Path(path).stat().st_mode):
        raise ValueError('saved report must be a regular file')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0))
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError('saved report must be a regular file')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            return stream.read(MAX_BYTES + 1)
    finally:
        os.close(fd)


def compare_sources(report, before, after):
    """Compare explicitly supplied bytes; never follow paths from report metadata."""
    mismatches = []
    for name, path in [('before', before), ('after', after)]:
        digest = hashlib.sha256()
        # Reject known special files before opening; recheck the opened descriptor.
        # Nonblocking open also prevents a regular-to-FIFO swap from waiting on POSIX.
        if not stat.S_ISREG(Path(path).stat().st_mode):
            raise ValueError('retained input must be a regular file')
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0))
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError('retained input must be a regular file')
            with os.fdopen(fd, 'rb', closefd=False) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
        finally:
            os.close(fd)
        if digest.hexdigest() != report[name + '_sha256']:
            mismatches.append(name)
    return mismatches


def render(report, counts_only=False, sources_checked=False):
    validate(report)
    def text(value):
        # Break opportunities add no text characters and need no CSS or script.
        # Escape each chunk independently so markup-like labels remain inert.
        # Leave Unicode words intact to avoid splitting grapheme sequences.
        return ''.join('<wbr>'.join(escape(word[i:i + 24])
                                   for i in range(0, len(word), 24))
                       if word.isascii() and not word.isspace() else escape(word)
                       for word in re.split(r'(\s+)', str(value)))

    def table(caption, headers, rows):
        return '<table><caption>' + text(caption) + '</caption><thead><tr>' + ''.join('<th scope="col">' + text(v) + '</th>' for v in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + text(v) + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table>'
    sections = []
    def heading(title, target, level=2):
        sections.append((target, title))
        return '<h' + str(level) + ' id="' + target + '">' + title + '</h' + str(level) + '>'

    c = report['counts']
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;">',
             '<title>Saved CSV change report</title><main><h1>Saved CSV change report</h1>',
             '<p>Local view of saved metadata. Internal totals checked; source authenticity has not been verified. No CSV cell values are included.</p>',
             heading('Record counts', 'record-counts') + '', table('Record counts', ['Measure', 'Records'], c.items()),
             heading('Changed cells by column', 'changed-columns') + '', table('Changed cells by column', ['Column', 'Changed cells'], report['changed_cells_by_column'].items())]
    if sources_checked:
        parts += [heading('Retained input comparison', 'retained-inputs') + '<p>Both explicitly supplied CSV files match the SHA-256 hashes saved in this JSON. This checks bytes only; it does not establish source authenticity, provenance or correctness of the reported differences. Files may change after comparison.</p>']
    if report.get('ignored_columns'):
        parts += [heading('Ignored columns', 'ignored-columns') + '<ul>' + ''.join('<li>' + text(n) + '</li>' for n in report['ignored_columns']) + '</ul>']
    if counts_only and report['format_version'] == 1:
        parts += [heading('Record positions', 'record-positions') + '<p>Counts-only view: record positions are intentionally hidden in this HTML, but remain in the saved detailed JSON. Zero details must not be inferred.</p>']
    elif report['format_version'] == 2:
        parts += [heading('Record positions', 'record-positions') + '<p>Summary only: record positions were omitted from this saved report. Zero details must not be inferred.</p>']
    else:
        parts += [heading('Record positions', 'record-positions') + '<p>Positions are 1-based data records, excluding the header; they are not physical line numbers when fields contain newlines.</p>']
        for field, title in [('added_after_records', 'Added positions in after CSV'), ('removed_before_records', 'Removed positions in before CSV')]:
            parts += [heading(title, field.replace('_', '-'), 3), table(title, ['Record'], ((n,) for n in report[field])) if report[field] else '<p>None</p>']
        parts += [heading('Changed records', 'changed-records', 3), table('Changed records', ['Before record', 'After record', 'Columns'], ((r['before_record'], r['after_record'], json.dumps(r['columns'], ensure_ascii=True)) for r in report['changed_records'])) if report['changed_records'] else '<p>None</p>']
    parts += [heading('Saved source hashes', 'source-hashes') + '', table('Saved source hashes', ['Input', 'SHA-256'], ((n, report[n + '_sha256']) for n in ('before', 'after'))), '<p>Tool version: ' + escape(report['tool_version']) + '</p></main></html>']
    navigation = '<nav aria-label="Report sections"><ul>' + ''.join(
        '<li><a href="#' + target + '">' + title + '</a></li>'
        for target, title in sections) + '</ul></nav>'
    parts.insert(5, navigation)
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', help='saved single-pair JSON report (not a batch manifest)')
    parser.add_argument('--output', required=True, help='new HTML file in a trusted directory; existing paths refused')
    parser.add_argument('--counts-only', action='store_true', help='omit record-position tables from HTML; keep counts and saved JSON unchanged')
    parser.add_argument('--before-csv', help='retained before CSV; requires --after-csv')
    parser.add_argument('--after-csv', help='retained after CSV; requires --before-csv')
    args = parser.parse_args()
    if bool(args.before_csv) != bool(args.after_csv):
        parser.error('--before-csv and --after-csv must be supplied together')
    try:
        raw = read_report_bytes(args.report)
        if len(raw) > MAX_BYTES:
            raise ValueError('oversize report')
        report = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
        validate(report)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
        print('E_REPORT: unreadable, unsupported or inconsistent report (8 MiB maximum); no HTML created.', file=sys.stderr)
        return 2
    if args.before_csv:
        try:
            mismatches = compare_sources(report, args.before_csv, args.after_csv)
        except (OSError, ValueError):
            print('E_SOURCE: cannot read supplied CSV files; no HTML created.', file=sys.stderr)
            return 2
        if mismatches:
            print('E_SOURCE: saved hash mismatch for ' + ', '.join(mismatches) + '; no HTML created.', file=sys.stderr)
            return 2
    html = render(report, counts_only=args.counts_only, sources_checked=bool(args.before_csv))
    try:
        target = Path(args.output)
        if os.path.lexists(target):
            raise FileExistsError()
        fd, temporary = tempfile.mkstemp(prefix='.csv-view-', dir=target.parent)
        committed = False
        cleanup_failed = False
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                stream.write(html)
            os.link(temporary, target)
            committed = True
        finally:
            try:
                os.unlink(temporary)
            except OSError:
                cleanup_failed = True
                print('E_OUTPUT: ' + json.dumps({
                    'error': ('complete HTML created but temporary cleanup failed'
                              if committed else 'temporary cleanup failed before HTML creation'),
                    'output_committed': committed,
                    'cleanup_required': True,
                    'recovery': ('Inspect the trusted output directory for .csv-view- siblings. '
                                 'Remove only files confirmed to belong to this run. '
                                 'Preserve any complete HTML; do not retry the same output path blindly.')
                }), file=sys.stderr)
        if cleanup_failed:
            return 2
    except (OSError, ValueError, RuntimeError):
        print('E_OUTPUT: cannot create new HTML; choose a fresh path in a trusted directory. Existing paths are refused; hard-link support is required.', file=sys.stderr)
        return 2
    print('Created local HTML review. Open it in your browser; it contains saved report metadata.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
