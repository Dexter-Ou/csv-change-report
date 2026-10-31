#!/usr/bin/env python3
"""Validate a data-only JSON manifest, then invoke the sequential batch runner."""
import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

MAX_MANIFEST_BYTES = 65536
MAX_PAIRS = 100


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate manifest field.')
        result[key] = value
    return result


def text(value):
    if not isinstance(value, str) or not value or any(
            ord(char) < 32 or 127 <= ord(char) <= 159 or 0xD800 <= ord(char) <= 0xDFFF
            for char in value):
        raise ValueError('Manifest strings must be nonempty and contain no control characters or surrogates.')
    return value


def load_manifest(path):
    # Nonblocking open refuses FIFOs without waiting for a writer. Symlinks to
    # regular files are allowed; this is not a filesystem sandbox.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Manifest must be a regular file.')
        raw = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError('Manifest exceeds 65536 bytes.')
    data = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_fields,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Invalid JSON constant.')))
    if not isinstance(data, dict) or set(data) != {'version', 'pairs'}:
        raise ValueError('Manifest requires exactly version and pairs.')
    if type(data['version']) is not int or data['version'] != 1:
        raise ValueError('Manifest version must be integer 1.')
    pairs = data['pairs']
    if not isinstance(pairs, list) or not 1 <= len(pairs) <= MAX_PAIRS:
        raise ValueError('Manifest requires between 1 and 100 pairs.')
    base = Path(os.path.abspath(path)).parent
    triples = []
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != {'before', 'after', 'key'}:
            raise ValueError('Each pair requires exactly before, after and key.')
        before, after, key = (text(pair[name]) for name in ('before', 'after', 'key'))
        # Preserve spelling, whitespace and CSV key exactly; no expansion/eval.
        triples.extend([os.path.join(str(base), before), os.path.join(str(base), after), key])
    return triples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-input-bytes', type=int, default=10485760)
    parser.add_argument('--ignore-column')
    parser.add_argument('--totals', action='store_true')
    parser.add_argument('manifest')
    parser.add_argument('new_report_dir', help='relative to current working directory')
    args = parser.parse_args()
    try:
        if not 1 <= args.max_input_bytes <= 10485760:
            raise ValueError('Input byte budget must be between 1 and 10485760.')
        if args.ignore_column is not None:
            text(args.ignore_column)
        triples = load_manifest(args.manifest)
        command = ['sh', str(Path(__file__).with_name('batch-review.sh').absolute()),
                   '--max-input-bytes', str(args.max_input_bytes)]
        if args.ignore_column is not None:
            command.append('--ignore-column')
            command.append(args.ignore_column)
        if args.totals:
            command.append('--totals')
        command.extend(['--', args.new_report_dir, *triples])
        return subprocess.run(command, check=False).returncode
    except (OSError, ValueError, RecursionError):
        # Avoid echoing untrusted manifest contents or file paths in diagnostics.
        print('Cannot run manifest: invalid/unreadable input or unavailable batch runner.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
