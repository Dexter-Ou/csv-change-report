#!/usr/bin/env python3
"""Compare two CSV exports without including cell contents in the report."""
import argparse
import csv
import hashlib
import io
import json
import os
import sys
from pathlib import Path

VERSION = '0.1.7-preview'

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 50000
MAX_COLUMNS = 256
MAX_CELLS = 250000


class InputError(ValueError):
    pass


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default diagnostic echoes supplied argument text.
        raise InputError('invalid arguments; use --help for usage')


def load(path, key):
    """Read one bounded snapshot; reject ambiguity instead of guessing."""
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise InputError('input exceeds 10 MiB limit')
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise InputError('input must be UTF-8') from None
    if '\x00' in text:
        raise InputError('NUL bytes are unsupported')
    try:
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        header = next(reader, None)
        if not header or any(not name.strip() for name in header):
            raise InputError('header is missing or contains blank names')
        if len(header) > MAX_COLUMNS:
            raise InputError('input exceeds 256 columns')
        if len(set(header)) != len(header):
            raise InputError('header names must be unique')
        if key not in header:
            raise InputError('key column is missing')
        key_index = header.index(key)
        rows = {}
        for number, row in enumerate(reader, 1):
            if number > MAX_ROWS:
                raise InputError('input exceeds 50000 records')
            if number * len(header) > MAX_CELLS:
                raise InputError('input exceeds 250000 data cells')
            if len(row) != len(header):
                raise InputError(f'record {number} has wrong field count')
            value = row[key_index]
            if not value.strip():
                raise InputError(f'record {number} has a blank key')
            if value in rows:
                raise InputError(f'record {number} repeats a key')
            rows[value] = (number, dict(zip(header, row)))
    except csv.Error:
        raise InputError('malformed CSV or field exceeds parser limit') from None
    return header, rows, hashlib.sha256(data).hexdigest()


def compare(before, after, key, ignore_columns=()):
    old_header, old, old_hash = load(before, key)
    new_header, new, new_hash = load(after, key)
    # Header order may differ; column additions/removals require explicit review.
    if set(old_header) != set(new_header):
        raise InputError('column sets differ; reconcile schemas before comparison')
    ignored = set(ignore_columns)
    if key in ignored:
        raise InputError('key column cannot be ignored')
    if not ignored.issubset(old_header):
        raise InputError('ignored column is missing')
    added = sorted(set(new) - set(old), key=lambda k: new[k][0])
    removed = sorted(set(old) - set(new), key=lambda k: old[k][0])
    changed = []
    unchanged = 0
    by_column = {name: 0 for name in old_header if name != key and name not in ignored}
    for value in sorted(set(old) & set(new), key=lambda k: old[k][0]):
        columns = [name for name in by_column if old[value][1][name] != new[value][1][name]]
        if columns:
            changed.append({'before_record': old[value][0], 'after_record': new[value][0],
                            'columns': columns})
            for name in columns:
                by_column[name] += 1
        else:
            unchanged += 1
    result = {
        'format_version': 1,
        'tool_version': VERSION,
        'before_sha256': old_hash,
        'after_sha256': new_hash,
        'counts': {'before': len(old), 'after': len(new), 'added': len(added),
                   'removed': len(removed), 'changed': len(changed), 'unchanged': unchanged},
        'added_after_records': [new[k][0] for k in added],
        'removed_before_records': [old[k][0] for k in removed],
        'changed_records': changed,
        'changed_cells_by_column': by_column,
    }
    if ignored:
        result['ignored_columns'] = [name for name in old_header if name in ignored]
    return result


def render_text(result):
    """Render metadata only; quote headers to escape terminal control characters."""
    counts = result['counts']
    lines = ['CSV Change Report ' + result['tool_version'],
             f"Records: before {counts['before']}, after {counts['after']}",
             f"Changes: added {counts['added']}, removed {counts['removed']}, "
             f"changed {counts['changed']}, unchanged {counts['unchanged']}"]
    if result.get('ignored_columns'):
        lines.append('Ignored columns: ' + ', '.join(
            json.dumps(name, ensure_ascii=True) for name in result['ignored_columns']))
    for label, records in [('Added after records', result['added_after_records']),
                           ('Removed before records', result['removed_before_records'])]:
        lines.append(label + ': ' + (', '.join(map(str, records)) or 'none'))
    lines.append('Changed records:')
    for record in result['changed_records']:
        columns = ', '.join(json.dumps(name, ensure_ascii=True) for name in record['columns'])
        lines.append(f"  before {record['before_record']} -> after {record['after_record']}: {columns}")
    if not result['changed_records']:
        lines.append('  none')
    lines.append('Changed cells by column:')
    for name, count in result['changed_cells_by_column'].items():
        lines.append('  ' + json.dumps(name, ensure_ascii=True) + ': ' + str(count))
    if not result['changed_cells_by_column']:
        lines.append('  none')
    return '\n'.join(lines)


def main(argv=None):
    parser = SafeArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('before')
    parser.add_argument('after')
    parser.add_argument('--key', required=True, help='exact, case-sensitive unique column name')
    parser.add_argument('--format', choices=('json', 'text'), default='json',
                        help='output format (default: json); text omits input hashes')
    parser.add_argument('--check', action='store_true',
                        help='exit 1 for added, removed or changed records; 0 when equal')
    parser.add_argument('--ignore-column', action='append', default=[], metavar='NAME',
                        help='ignore one exact non-key column; repeat for multiple columns')
    parser.add_argument('--output', help='create a new report file; existing paths are refused')
    try:
        parser.add_argument('--version', action='version',
                            version=f'csv-change-report {VERSION}')
        args = parser.parse_args(argv)
        result = compare(args.before, args.after, args.key, args.ignore_column)
    except (InputError, OSError) as error:
        # Do not echo file paths or cell values in diagnostics.
        message = str(error) if isinstance(error, InputError) else 'input file could not be read'
        print(json.dumps({'error': message}), file=sys.stderr)
        return 2
    status = int(args.check and any(result['counts'][name]
                                    for name in ('added', 'removed', 'changed')))
    report = (render_text(result) if args.format == 'text' else
              json.dumps(result, indent=2, ensure_ascii=True)) + '\n'
    if args.output is None:
        try:
            sys.stdout.write(report)
            sys.stdout.flush()
        except (OSError, RuntimeError):
            print(json.dumps({'error': 'standard output could not be written'}), file=sys.stderr)
            return 2
        return status
    try:
        target = Path(args.output)
        if target.resolve() in (Path(args.before).resolve(), Path(args.after).resolve()):
            raise InputError('output path matches an input')
        # O_EXCL rejects existing paths, including dangling symlinks. No truncation.
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(report)
    except (InputError, OSError, RuntimeError) as error:
        message = (str(error) if isinstance(error, InputError) else
                   'output path already exists' if isinstance(error, FileExistsError) else
                   'output file could not be written')
        print(json.dumps({'error': message}), file=sys.stderr)
        return 2
    return status


if __name__ == '__main__':
    status = main()
    if status == 2:
        # Avoid a failed buffered stdout flush overriding exit 2 at shutdown.
        try:
            stdout_fd = None
            fd = os.open(os.devnull, os.O_WRONLY)
            try:
                stdout_fd = sys.stdout.fileno()
                os.dup2(fd, stdout_fd)
            finally:
                if fd != stdout_fd:
                    os.close(fd)
        except (OSError, ValueError, AttributeError):
            sys.stdout = None
    sys.exit(status)
