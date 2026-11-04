# Optional aggregate statistics recipe

Requires Python 3.10+ standard library and an existing CSV Change JSON report.

    python3 evaluation/report_stats.py report.json

The recipe accepts detailed or summary reports with the six existing count fields.
It prints two separate measures, never one combined “percent different”:

- Original records changed or removed: (changed + removed) / before × 100.
- Final records newly added: added / after × 100.

For before=2, after=2, changed=1, removed=1, added=1, unchanged=0,
these are 100.00% and 50.00%. Do not add these percentages: their populations
and denominators differ. Changed means a matched key with at least one changed
non-key field; this is a record measure, not a cell-change percentage. Key edits
may appear as removal/addition under the configured matching key.

An empty denominator displays N/A, represented by null in the Python result.
The recipe checks nonnegative integer counts and both conservation identities;
it does not verify that a report is genuine or matches the CSV files. It reads
but does not modify the report, and outputs no cell values or column names.
Read a report only from a trusted local path; normal filesystem access applies.

Tested on the isolated Linux worker with eight synthetic fixture pairs from the
retained release archive and two invalid-count fixtures. Other platforms have not been tested.
The recipe does not change the CSV Change report schema.

Summary mode removes record-detail lists, not the six count fields used here.
The retained summary-mode compatibility fixture is synthetic, not customer data.
This optional script prints a separate human-readable interpretation; it does not
add fields to CSV Change JSON or change csv_change.py exit-code behavior.
