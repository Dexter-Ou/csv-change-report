# 0.1.6-preview

Fixes reproduced stdout failures: closed pipes previously exited 120, direct
write exceptions escaped, and main() did not detect flush failures. Report stdout
is now explicitly flushed; detected write/flush errors take precedence over
--check and return 2 with a fixed diagnostic. CLI shutdown discards failed
buffered output to preserve status 2. Healthy content remains the same except
for tool_version. Two regression methods add injected stream and Linux closed
pipe coverage. No downstream delivery/durability guarantee; no Windows test.

Run with Python 3 and no external dependencies: python3 -m unittest -v.
Run sh evaluation/review.sh examples/before.csv examples/after.csv id.
These are synthetic checks, not independent user validation or revenue.
