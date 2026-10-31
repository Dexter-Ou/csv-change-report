#!/bin/sh
# Offline, sequential batch review. No dependency installation or network access.
set -eu
if [ "$#" -lt 4 ] || [ $(( ($# - 1) % 3 )) -ne 0 ]; then
    echo 'Usage: sh batch-review.sh NEW_REPORT_DIR BEFORE AFTER KEY [BEFORE AFTER KEY ...]' >&2
    exit 2
fi
kit_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
report_dir=$1
shift
# Prefix relative paths so a leading dash cannot become a mkdir option.
case "$report_dir" in /*) ;; *) report_dir=./$report_dir ;; esac
if ! (umask 077; mkdir "$report_dir"); then
    echo 'Cannot create a new report directory; choose an unused path.' >&2
    exit 2
fi
printf 'pair\tstatus\treport\tdiagnostic\n' > "$report_dir/status.tsv"
pair=0
batch_status=0
while [ "$#" -gt 0 ]; do
    pair=$((pair + 1))
    stem=$(printf 'pair-%04d' "$pair")
    before=$1
    after=$2
    key=$3
    shift 3
    case "$before" in /*) ;; *) before=./$before ;; esac
    case "$after" in /*) ;; *) after=./$after ;; esac
    status=0
    python3 "$kit_dir/../csv_change.py" "$before" "$after" --key "$key" --check --summary-only \
        --output "$report_dir/$stem.json" > "$report_dir/$stem.stdout" 2> "$report_dir/$stem.stderr" || status=$?
    report=-
    case "$status" in
        0) report=$stem.json ;;
        1) report=$stem.json
           if [ "$batch_status" -eq 0 ]; then batch_status=1; fi ;;
        *) batch_status=2 ;;
    esac
    printf '%s\t%s\t%s\t%s\n' "$stem" "$status" "$report" "$stem.stderr" >> "$report_dir/status.tsv"
done
exit "$batch_status"
