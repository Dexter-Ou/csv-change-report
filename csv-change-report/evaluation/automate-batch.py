#!/usr/bin/env python3
"""Run checked manifest preflight, comparison and status-table verification offline."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


class Parser(argparse.ArgumentParser):
    def error(self, message):
        emit('E_ARGUMENTS', 2)
        raise SystemExit(2)


def emit(code, status, pair_count=None):
    print(json.dumps({'version': 1, 'code': code, 'status': status,
                      'pair_count': pair_count}, sort_keys=True))
    return status


def invoke(arguments):
    return subprocess.run([sys.executable, *map(str, arguments)],
                          capture_output=True, check=False)


def accepted_preflight(result):
    metadata = json.loads(result.stdout)
    expected = {'version': 1, 'valid': True, 'code': 'OK',
                'csv_files_checked': False, 'reports_created': False}
    return (result.returncode == 0 and type(metadata) is dict
            and metadata.keys() == expected.keys() | {'pair_count'}
            and all(type(metadata[k]) is type(v) and metadata[k] == v
                    for k, v in expected.items())
            and type(metadata['pair_count']) is int
            and 1 <= metadata['pair_count'] <= 100), metadata


def main():
    parser = Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument('manifest')
    parser.add_argument('reports', help='new report directory; parent must exist')
    args = parser.parse_args()
    helpers = Path(__file__).resolve().parent
    manifest = Path(args.manifest).absolute()
    reports = Path(args.reports).absolute()
    try:
        preflight = invoke([helpers / 'batch-manifest.py', '--validate-only',
                            '--json', '--', manifest])
        accepted, metadata = accepted_preflight(preflight)
    except (OSError, ValueError, TypeError, KeyError):
        return emit('E_PREFLIGHT', 2)
    if not accepted:
        return emit('E_PREFLIGHT', 2)
    count = metadata['pair_count']
    try:
        if reports.exists() or reports.is_symlink():
            return emit('E_OUTPUT', 2, count)
        comparison = invoke([helpers / 'batch-manifest.py', '--', manifest, reports])
        if comparison.returncode not in (0, 1, 2):
            return emit('E_EXECUTION', 2, count)
        totals_run = invoke([helpers / 'batch-totals.py', reports / 'status.tsv',
                             '--expected-pairs', count])
        totals = json.loads(totals_run.stdout)
        keys = {'expected', 'completed', 'equal', 'changed', 'error', 'incomplete'}
        if (type(totals) is not dict or totals.keys() != keys
                or any(type(v) is not int or v < 0 for v in totals.values())
                or totals['expected'] != count or totals['completed'] != count
                or totals['incomplete'] != 0
                or totals['equal'] + totals['changed'] + totals['error'] != count):
            return emit('E_STATUS', 2, count)
        status = 2 if totals['error'] else 1 if totals['changed'] else 0
        if comparison.returncode != status or totals_run.returncode != status:
            return emit('E_STATUS', 2, count)
    except (OSError, ValueError, TypeError, KeyError):
        return emit('E_STATUS', 2, count)
    return emit('E_COMPARISON' if status == 2 else 'CHANGED' if status else 'EQUAL',
                status, count)


if __name__ == '__main__':
    sys.exit(main())
