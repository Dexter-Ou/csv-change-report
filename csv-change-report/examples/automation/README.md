# Use --check in a local shell workflow

Run from the product folder containing csv_change.py. Requires Python 3.10+
and a POSIX shell. This recipe is local; it installs no scheduler or hosted CI.
The included check-exports.sh is under examples/automation/.
The examples reuse fictional exports under examples/stable-key/.

```sh
sh examples/automation/check-exports.sh examples/stable-key/before.csv examples/stable-key/before.csv id
sh examples/automation/check-exports.sh examples/stable-key/before.csv examples/stable-key/after-corrected.csv id
sh examples/automation/check-exports.sh examples/stable-key/before.csv examples/stable-key/after-blank.csv id
```

Run separately: expected statuses are 0 (UNCHANGED), 1 (CHANGED), and 2
(INVALID). The wrapper preserves the tool's status and diagnostic streams.
With `set -e`, calling it as a bare command stops the caller on status 1 as
well as status 2. Capture the status explicitly when branching:

```sh
set -eu
status=0
sh examples/automation/check-exports.sh examples/stable-key/before.csv examples/stable-key/after-corrected.csv id || status=$?
case "$status" in
    0) printf '%s\n' 'Continue: exports match.' ;;
    1) printf '%s\n' 'Pause for local review.' ;;
    *) printf '%s\n' 'Stop: resolve the comparison error.' >&2; exit "$status" ;;
esac
```

Do not use `if ! command; then status=$?`: that captures the negation's status,
not the tool's. Do not use `|| true` when a later step needs the outcome.
The script quotes paths and key names; supply exactly three arguments.
Missing files, blank/duplicate keys and invalid options are errors, never
"unchanged". Unexpected process failures retain their original exit status.

`--check` creates no report and does not edit inputs. For a review report, run
csv_change.py separately with a fresh --output filename after resolving errors.
Keep original exports; check source corrections rather than inventing keys.
No automatic upload, email, purchase or data correction occurs. A detected
change says nothing about whether a business action is appropriate.
