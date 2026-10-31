# 0.1.9-preview candidate

Adds --max-input-bytes N for a smaller per-input raw-byte budget, with the
existing 10 MiB ceiling retained. Exact-limit inputs are accepted if valid;
over-limit inputs fail with status 2 before report creation. Defaults and
report formats remain unchanged apart from the tool version.

Run python3 -m unittest -v and evaluation/review.sh. Synthetic boundary tests
cover both inputs, UTF-8/BOM/CRLF bytes, output and input preservation, invalid
arguments and bounded reads. This is not a total-memory or crash-durability
guarantee. No new dependencies or services. Independent usefulness and
willingness to pay remain unverified.
