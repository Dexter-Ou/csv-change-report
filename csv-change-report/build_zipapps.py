#!/usr/bin/env python3
"""Build two standalone Python archives using only the standard library."""
import argparse
from pathlib import Path
import sys
import zipfile


def build(destination):
    source = Path(__file__).resolve().parent
    # Read all inputs before claiming a new destination directory.
    license_bytes = (source / 'LICENSE').read_bytes()
    programs = [(name, (source / name).read_bytes())
                for name in ('csv_change.py', 'view_report.py')]
    destination.mkdir()  # Exclusive directory creation; never overwrite a build.
    for name, program in programs:
        with zipfile.ZipFile(destination / (Path(name).stem + '.pyz'), 'x',
                             compression=zipfile.ZIP_STORED) as archive:
            for entry, content in [('__main__.py', program), ('LICENSE', license_bytes)]:
                info = zipfile.ZipInfo(entry, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='new directory; parent must exist')
    args = parser.parse_args()
    try:
        build(args.destination)
    except (OSError, ValueError, zipfile.BadZipFile):
        print('Build refused or failed. Preserve any output directory; choose a new '
              'destination after inspection. Existing destinations are never reused.',
              file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
