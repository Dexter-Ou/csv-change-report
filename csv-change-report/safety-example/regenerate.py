"""Regenerate this fictional example using an adjacent product directory."""
from pathlib import Path
import subprocess
import sys

example = Path(__file__).resolve().parent
product = example.parent
ignored = '<iframe src="https://example.invalid/ignored">'
commands = [
    [str(product / "csv_change.py"), str(example / "before.csv"),
     str(example / "after.csv"), "--key", "id", "--ignore-column", ignored,
     "--output", str(example / "new-report.json")],
    [str(product / "view_report.py"), str(example / "new-report.json"),
     "--before-csv", str(example / "before.csv"), "--after-csv",
     str(example / "after.csv"), "--output", str(example / "new-report.html")],
]
for command in commands:
    result = subprocess.run([sys.executable, "-B", *command], check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
print("Open safety-example/new-report.html locally to review the output.")
