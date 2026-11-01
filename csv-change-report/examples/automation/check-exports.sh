#!/bin/sh
# Run from the product directory containing csv_change.py.
set -eu
if [ "$#" -ne 3 ]; then
    printf '%s\n' 'Usage: sh check-exports.sh BEFORE.csv AFTER.csv KEY' >&2
    exit 2
fi
status=0
python3 csv_change.py "$1" "$2" --key "$3" --check || status=$?
case "$status" in
    0) printf '%s\n' 'UNCHANGED: no differences detected.' ;;
    1) printf '%s\n' 'CHANGED: review the exports before taking action.' ;;
    2) printf '%s\n' 'INVALID: comparison failed; inspect stderr and original exports.' >&2 ;;
    *) printf '%s\n' 'FAILED: unexpected process status; inspect stderr.' >&2 ;;
esac
exit "$status"
