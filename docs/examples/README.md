# Synthetic CSV export report

Download [`synthetic-export-review.html`](synthetic-export-review.html) using
GitHub's raw/download control, then open the saved file in your local browser.
GitHub's source view is not a rendered preview. No Python is needed to inspect
this saved example. It uses the included synthetic CSV fixtures, not customer data.

Expect 3 records in each input: 1 added, 1 removed, 1 changed and 1 unchanged.
The changed column is `status`, at data record 1 in both inputs. Added and removed
positions are record 2. Positions exclude the header. No CSV cell values appear.

This file was generated with the [pinned 0.1.10-preview source](https://github.com/Dexter-Ou/csv-change-report/tree/708201fee61caeac4f29dc99d982460e95e5390d),
using the two commands in the [compare-to-HTML walkthrough](../COMPARE-CSV-EXPORTS.md#save-a-report-and-open-it-as-html).
The retained-input statement records a hash match during generation; opening
this saved HTML does not recheck files on your computer. Byte matching does not
prove authenticity, provenance or correctness of the reported differences.

The HTML contains no scripts or external resources. It still exposes column
names, counts, positions and source hashes. Hashes are not anonymization; review
your own reports before sharing. Synthetic Linux command and HTML parser checks
are not browser appearance, accessibility or Windows/macOS validation.
