#!/usr/bin/env python3
"""Validate a data-only JSON manifest, optionally without running comparisons."""
import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

MAX_MANIFEST_BYTES = 65536
MAX_PAIRS = 100
MAX_JSON_DEPTH = 32

# Fixed diagnostics only: never interpolate input values, paths or exceptions.
REASONS = {
    'E_ARGUMENTS': 'Check options; supply a manifest and, unless validating only, a report directory.',
    'E_BUDGET': 'Set --max-input-bytes to an integer from 1 to 10485760.',
    'E_READ': 'Check that the manifest exists and is readable.',
    'E_FILE': 'Use a regular file for the manifest.',
    'E_SIZE': 'Reduce the manifest to at most 65536 bytes.',
    'E_ENCODING': 'Save the manifest as UTF-8.',
    'E_BOM': 'Save a separate UTF-8 copy without the leading BOM in the same directory; see evaluation/RECOVERY.md.',
    'E_JSON': 'Use valid JSON without nonstandard constants.',
    'E_DEPTH': 'Reduce JSON nesting to at most 32 levels.',
    'E_DUPLICATE': 'Remove duplicate JSON object fields.',
    'E_SCHEMA': 'Use exactly version and pairs at the top level.',
    'E_VERSION': 'Set version to the integer 1.',
    'E_PAIRS': 'Supply a list containing 1 to 100 pairs.',
    'E_PAIR': 'Use exactly before, after and key in every pair.',
    'E_TEXT': 'Use nonempty strings without controls or surrogate characters.',
    'E_RUNNER': 'Check the bundled shell runner and shell availability.',
}


class ManifestError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def diagnostic(code):
    print('Cannot run manifest [' + code + ']: ' + REASONS[code], file=sys.stderr)


def json_result(code, pair_count=None):
    # Only fixed metadata; never include supplied paths, keys or exception text.
    print(json.dumps({'version': 1, 'valid': code == 'OK', 'code': code,
                      'pair_count': pair_count, 'csv_files_checked': False,
                      'reports_created': False}, sort_keys=True))


class SafeParser(argparse.ArgumentParser):
    json_output = False

    def error(self, message):
        if self.json_output:
            json_result('E_ARGUMENTS')
        diagnostic('E_ARGUMENTS')
        raise SystemExit(2)



def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError('E_DUPLICATE')
        result[key] = value
    return result


def text(value):
    if not isinstance(value, str) or not value or any(
            ord(char) < 32 or 127 <= ord(char) <= 159 or 0xD800 <= ord(char) <= 0xDFFF
            for char in value):
        raise ManifestError('E_TEXT')
    return value


def check_depth(document):
    # Count structural brackets only outside strings. JSON parsing below still
    # validates syntax; this pass bounds nesting before the parser sees it.
    depth = 0
    quoted = escaped = False
    for char in document:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ManifestError('E_DEPTH')
        elif char in ']}':
            depth -= 1


def load_manifest(path):
    # Nonblocking open refuses FIFOs without waiting for a writer. Symlinks to
    # regular files are allowed; this is not a filesystem sandbox.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ManifestError('E_FILE')
        raw = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ManifestError('E_SIZE')
    document = raw.decode('utf-8')
    if document.startswith('\ufeff'):
        raise ManifestError('E_BOM')
    check_depth(document)
    data = json.loads(document, object_pairs_hook=unique_fields,
                      parse_constant=lambda _: (_ for _ in ()).throw(ManifestError('E_JSON')))
    if not isinstance(data, dict) or set(data) != {'version', 'pairs'}:
        raise ManifestError('E_SCHEMA')
    if type(data['version']) is not int or data['version'] != 1:
        raise ManifestError('E_VERSION')
    pairs = data['pairs']
    if not isinstance(pairs, list) or not 1 <= len(pairs) <= MAX_PAIRS:
        raise ManifestError('E_PAIRS')
    base = Path(os.path.abspath(path)).parent
    triples = []
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != {'before', 'after', 'key'}:
            raise ManifestError('E_PAIR')
        before, after, key = (text(pair[name]) for name in ('before', 'after', 'key'))
        # Preserve spelling, whitespace and CSV key exactly; no expansion/eval.
        triples.extend([os.path.join(str(base), before), os.path.join(str(base), after), key])
    return triples


def main():
    parser = SafeParser(description=__doc__, allow_abbrev=False)
    # Detect the exact flag before parsing so argument failures also use JSON.
    # A literal -- ends option parsing; a filename after it is not a flag.
    options = sys.argv[1:]
    options = options[:options.index('--')] if '--' in options else options
    parser.json_output = '--json' in options
    parser.add_argument('--max-input-bytes', type=int, default=10485760)
    parser.add_argument('--ignore-column')
    parser.add_argument('--totals', action='store_true')
    parser.add_argument('--validate-only', action='store_true',
                        help='validate and resolve manifest only; do not read CSVs or create reports')
    parser.add_argument('--json', action='store_true',
                        help='emit versioned JSON metadata; requires --validate-only')
    parser.add_argument('manifest')
    parser.add_argument('new_report_dir', nargs='?', help='required for execution; relative to current working directory')
    args = parser.parse_args()
    if args.json and not args.validate_only:
        parser.error('--json requires --validate-only')
    if not args.validate_only and args.new_report_dir is None:
        parser.error('report directory required')
    try:
        if not 1 <= args.max_input_bytes <= 10485760:
            raise ManifestError('E_BUDGET')
        if args.ignore_column is not None:
            text(args.ignore_column)
        triples = load_manifest(args.manifest)
        if args.validate_only:
            if args.json:
                json_result('OK', len(triples) // 3)
            else:
                print('Manifest valid: ' + str(len(triples) // 3) +
                      ' pair(s); CSV files not checked; no reports created.')
            return 0
        command = ['sh', str(Path(__file__).with_name('batch-review.sh').absolute()),
                   '--max-input-bytes', str(args.max_input_bytes)]
        if args.ignore_column is not None:
            command.append('--ignore-column')
            command.append(args.ignore_column)
        if args.totals:
            command.append('--totals')
        command.extend(['--', args.new_report_dir, *triples])
    except ManifestError as exc:
        code = exc.code
    except UnicodeError:
        code = 'E_ENCODING'
    except RecursionError:
        code = 'E_DEPTH'
    except ValueError:
        code = 'E_JSON'
    except IsADirectoryError:
        code = 'E_FILE'
    except OSError:
        code = 'E_READ'
    else:
        code = None
    if code is not None:
        if args.json:
            json_result(code)
        diagnostic(code)
        return 2
    try:
        return subprocess.run(command, check=False).returncode
    except OSError:
        diagnostic('E_RUNNER')
        return 2


if __name__ == '__main__':
    sys.exit(main())
