#!/bin/sh
# Offline, sequential batch review. No dependency installation or network access.
set -eu
max_input_bytes=10485760
ignore_column=
seen_budget=0
seen_ignore=0
write_totals=0
while :; do
    case "${1-}" in
        --max-input-bytes)
            if [ "$#" -lt 2 ] || [ "$seen_budget" -eq 1 ]; then
                echo 'Missing or repeated input byte budget.' >&2; exit 2
            fi
            max_input_bytes=$2
            case "$max_input_bytes" in
                ''|0*|*[!0-9]*) echo 'Invalid input byte budget.' >&2; exit 2 ;;
            esac
            if [ "${#max_input_bytes}" -gt 8 ] || [ "$max_input_bytes" -gt 10485760 ]; then
                echo 'Input byte budget must be between 1 and 10485760.' >&2; exit 2
            fi
            seen_budget=1
            shift 2 ;;
        --ignore-column)
            if [ "$#" -lt 2 ] || [ -z "$2" ] || [ "$seen_ignore" -eq 1 ]; then
                echo 'Missing, empty or repeated ignored column.' >&2; exit 2
            fi
            ignore_column=$2
            seen_ignore=1
            shift 2 ;;
        --totals)
            if [ "$write_totals" -eq 1 ]; then
                echo 'Repeated totals option.' >&2; exit 2
            fi
            write_totals=1
            shift ;;
        --) shift; break ;;
        *) break ;;
    esac
done
run_compare() {
    if [ "$seen_ignore" -eq 1 ]; then
        python3 "$kit_dir/../csv_change.py" "$@" "--ignore-column=$ignore_column"
    else
        python3 "$kit_dir/../csv_change.py" "$@"
    fi
}
if [ "$#" -lt 4 ] || [ $(( ($# - 1) % 3 )) -ne 0 ]; then
    echo 'Usage: sh batch-review.sh [--max-input-bytes N] [--ignore-column COLUMN] [--totals] [--] NEW_REPORT_DIR BEFORE AFTER KEY [BEFORE AFTER KEY ...]' >&2
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
    run_compare "$before" "$after" --key "$key" --check --summary-only --max-input-bytes "$max_input_bytes" \
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
if [ "$write_totals" -eq 1 ]; then
    totals_status=0
    python3 "$kit_dir/batch-totals.py" "$report_dir/status.tsv" --expected-pairs "$pair" --row-counts \
        > "$report_dir/totals.json.tmp" 2> "$report_dir/totals.stderr" || totals_status=$?
    if [ -s "$report_dir/totals.json.tmp" ] && [ "$totals_status" -le 2 ]; then
        mv "$report_dir/totals.json.tmp" "$report_dir/totals.json"
    else
        rm -f "$report_dir/totals.json.tmp"
        totals_status=2
    fi
    if [ "$totals_status" -eq 2 ]; then batch_status=2; fi
fi
exit "$batch_status"
