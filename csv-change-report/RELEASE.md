# 0.1.8-preview

Adds optional --summary-only in JSON and text. Retains counts, per-column totals,
exclusions, full-byte JSON hashes and check statuses; omits record positions and
per-record column lists. Summary JSON uses format_version 2 and report_mode
summary. Detailed mode remains the default with format_version 1.

Run python3 -m unittest -v and evaluation/review.sh. Synthetic tests include
summary parity, omission, output preservation and a 10,000-record changed diff.
No streaming, independent user validation, Windows/macOS, hostile-directory or
crash-durability assurance. No dependencies, telemetry or hosted service added.
