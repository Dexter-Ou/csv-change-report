#!/usr/bin/env python3
"""Create a private offline HTML index after all batch writers have stopped."""
import argparse
import html
from pathlib import Path
import runpy
import sys


def available(directory, name):
    path = directory / name
    return not path.is_symlink() and path.is_file()


def render(directory, expected):
    if not 1 <= expected <= 100:
        raise ValueError('expected pairs must be between 1 and 100')
    table = directory / 'status.tsv'
    if not available(directory, 'status.tsv') or table.stat().st_size > 65536:
        raise ValueError('status table must be a small regular file')
    reader = runpy.run_path(str(Path(__file__).with_name('batch-totals.py')))
    totals, rows = reader['validated_table'](table, expected)
    schema = runpy.run_path(str(Path(__file__).with_name('report_schema.py')))
    body = []
    problems = bool(totals['error'] or totals['incomplete'])
    for index in range(1, expected + 1):
        stem = f'pair-{index:04d}'
        links = []
        label = 'INCOMPLETE — no completed status row'
        if index <= len(rows):
            _, status, report, diagnostic = rows[index - 1]
            label = {'0': 'EQUAL', '1': 'CHANGED'}.get(status, 'ERROR — comparison failed')
            if status in ('0', '1'):
                try:
                    if not available(directory, report) or (directory / report).stat().st_size > 1048576:
                        raise ValueError('report unavailable')
                    schema['validate_summary'](directory / report, status)
                    links.append(f'<a href="{report}">JSON summary</a>')
                except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
                    label = 'ERROR — missing or invalid summary'
                    problems = True
            if available(directory, diagnostic):
                links.append(f'<a href="{diagnostic}">Diagnostic</a>')
            else:
                label += '; diagnostic missing or unsafe'
                problems = True
        body.append(f'<tr><th scope="row">{stem}</th><td>{html.escape(label)}</td><td>{" · ".join(links) or "—"}</td></tr>')
    counts = ', '.join(f'{name}={totals[name]}' for name in ('expected', 'completed', 'equal', 'changed', 'error', 'incomplete'))
    page = '<!doctype html><html lang="en"><meta charset="utf-8">' + \
        '<meta name="viewport" content="width=device-width, initial-scale=1">' + \
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; base-uri &#39;none&#39;">' + \
        '<title>CSV batch results</title><h1>CSV batch results</h1>' + \
        '<p>Offline snapshot. Expected pair count supplied by the operator. No CSV provenance or concurrent-write verification. Keep reports and diagnostics private.</p>' + \
        '<p>' + counts + '</p><p>' + ('Review required: errors, incomplete pairs or unavailable files.' if problems else 'All expected pairs have valid summaries and diagnostics.') + \
        '</p><table><caption>Pair results and local files</caption><thead><tr><th scope="col">Pair</th><th scope="col">Result</th><th scope="col">Files</th></tr></thead><tbody>' + ''.join(body) + '</tbody></table></html>\n'
    return page, 2 if problems else 1 if totals['changed'] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--expected-pairs', type=int, required=True)
    args = parser.parse_args()
    try:
        page, status = render(args.directory, args.expected_pairs)
        # Exclusive creation preserves existing files, including dangling symlinks.
        with (args.directory / 'index.html').open('x', encoding='utf-8') as stream:
            stream.write(page)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
        print('Cannot create index: preserve the directory and inspect table, files and output path.', file=sys.stderr)
        return 2
    print('Created index.html; status 0=equal, 1=changed, 2=review required.')
    return status


if __name__ == '__main__':
    sys.exit(main())
