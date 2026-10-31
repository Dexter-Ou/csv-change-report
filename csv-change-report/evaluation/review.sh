#!/bin/sh
# Run from any working directory. Paths are quoted; Python 3.10+ is required.
set -eu
if [ "$#" -ne 3 ]; then
    echo 'Usage: sh review.sh BEFORE.csv AFTER.csv KEY' >&2
    exit 2
fi
kit_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
status=0
python3 "$kit_dir/../csv_change.py" "$1" "$2" --key "$3" --check --format text || status=$?
case "$status" in
    0) echo 'No keyed content changes; comparison completed.' ;;
    1) echo 'Content changed; review the report above before using the export.' ;;
    *) echo 'Comparison failed; do not treat any report as completed.' >&2
       exit "$status" ;;
esac
# Both completed review outcomes are successful script runs. The raw CLI uses 1
# for changes; this wrapper deliberately consumes that status after showing it.
