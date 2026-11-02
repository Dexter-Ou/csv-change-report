"""Generate fictional CSV exports in a NEW directory. Python standard library only."""
import argparse
import csv
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="new output directory; existing paths are refused")
    args = parser.parse_args()
    try:
        args.directory.mkdir()
    except FileExistsError:
        parser.error("output directory already exists; choose a new path")
    fields = ["stock_id", "sku", "bin", "quantity", "status"]
    before = [dict(zip(fields, [f"S{i:05}", f"ITEM{i:05}", f"B{i%100:03}", str(i%200), "available"])) for i in range(10000)]
    after = [dict(row) for row in before[100:]]
    for row in after:
        i = int(row["stock_id"][1:])
        if 100 <= i < 300:
            row["quantity"] = str(int(row["quantity"]) + 1)
        if 300 <= i < 400:
            row["status"] = "hold"
    after.extend(dict(zip(fields, [f"S{i:05}", f"ITEM{i:05}", "B999", "1", "available"])) for i in range(10000, 10100))
    after.reverse()
    for name, rows in [("before.csv", before), ("after.csv", after), ("reordered.csv", list(reversed(before)))]:
        with (args.directory / name).open("x", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print("Created three fictional 10,000-row CSVs in", args.directory)

if __name__ == "__main__":
    main()
