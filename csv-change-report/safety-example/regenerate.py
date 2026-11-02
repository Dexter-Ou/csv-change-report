"""Regenerate this fictional example using an adjacent product directory."""
from pathlib import Path
import subprocess
import sys

example = Path(__file__).resolve().parent
product = example.parent
# Refuse predictable failures before either output is created. The child tools
# still perform exclusive output creation; this preflight is not a transaction.
for name in ("new-report.json", "new-report.html"):
    output = example / name
    if output.exists() or output.is_symlink():
        print(f"Output already exists: {output}", file=sys.stderr)
        raise SystemExit(2)
for source in (product / "csv_change.py", product / "view_report.py",
               example / "before.csv", example / "after.csv"):
    if not source.is_file():
        print(f"Required source file missing: {source}", file=sys.stderr)
        raise SystemExit(2)
ignored = '<iframe src="https://example.invalid/ignored">'
commands = [
    [str(product / "csv_change.py"), str(example / "before.csv"),
     str(example / "after.csv"), "--key", "id", "--ignore-column", ignored,
     "--output", str(example / "new-report.json")],
    [str(product / "view_report.py"), str(example / "new-report.json"),
     "--before-csv", str(example / "before.csv"), "--after-csv",
     str(example / "after.csv"), "--output", str(example / "new-report.html")],
]
for stage, command in enumerate(commands):
    result = subprocess.run([sys.executable, "-B", *command], check=False)
    if result.returncode:
        if stage == 1:
            print("Viewer failed. Any generated outputs have been left in place. "
                  f"Inspect {example / 'new-report.json'} and "
                  f"{example / 'new-report.html'} before moving or removing "
                  "generated files and rerunning.", file=sys.stderr)
        raise SystemExit(result.returncode)
print("Open safety-example/new-report.html locally to review the output.")
