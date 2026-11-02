# CSV Change: recorded terminal tour

Synthetic Linux command run against published package 6dffce2b04e7e5b88100287611773e500ae0e6d9.
These invented records are not customers or business inventory. This is a text transcript, not a terminal screenshot or browser test.
Run from the extracted csv-change-report directory with Python 3.10+. No install, network or account is needed.
Exit 0 normally means comparison succeeded, even when changes exist. --check uses 0=equal, 1=changed, 2=error.
Reports omit cell values; column names, counts and positions may still be sensitive. Inspect original records locally.

## Detailed text

```text
$ python3 csv_change.py examples/before.csv examples/after.csv --key id --format text
CSV Change Report 0.1.10-preview
Records: before 3, after 3
Changes: added 1, removed 1, changed 1, unchanged 1
Added after records: 2
Removed before records: 2
Changed records:
  before 1 -> after 1: "status"
Changed cells by column:
  "name": 0
  "status": 1
(stderr empty)
exit status: 0
```

## Detailed JSON

```text
$ python3 csv_change.py examples/before.csv examples/after.csv --key id
{
  "format_version": 1,
  "tool_version": "0.1.10-preview",
  "before_sha256": "47a72c33f86207715fd3f1784d61f65e5449307dee4fa565d11e54560c625e88",
  "after_sha256": "73668cd0ab11b7c6ea1763637371875fd99c611ab859352c648ca27fd7129235",
  "counts": {
    "before": 3,
    "after": 3,
    "added": 1,
    "removed": 1,
    "changed": 1,
    "unchanged": 1
  },
  "added_after_records": [
    2
  ],
  "removed_before_records": [
    2
  ],
  "changed_records": [
    {
      "before_record": 1,
      "after_record": 1,
      "columns": [
        "status"
      ]
    }
  ],
  "changed_cells_by_column": {
    "name": 0,
    "status": 1
  }
}
(stderr empty)
exit status: 0
```

## Summary JSON

```text
$ python3 csv_change.py examples/before.csv examples/after.csv --key id --summary-only
{
  "format_version": 2,
  "tool_version": "0.1.10-preview",
  "before_sha256": "47a72c33f86207715fd3f1784d61f65e5449307dee4fa565d11e54560c625e88",
  "after_sha256": "73668cd0ab11b7c6ea1763637371875fd99c611ab859352c648ca27fd7129235",
  "counts": {
    "before": 3,
    "after": 3,
    "added": 1,
    "removed": 1,
    "changed": 1,
    "unchanged": 1
  },
  "changed_cells_by_column": {
    "name": 0,
    "status": 1
  },
  "report_mode": "summary"
}
(stderr empty)
exit status: 0
```

## Changed check

```text
$ python3 csv_change.py examples/before.csv examples/after.csv --key id --check --summary-only
{
  "format_version": 2,
  "tool_version": "0.1.10-preview",
  "before_sha256": "47a72c33f86207715fd3f1784d61f65e5449307dee4fa565d11e54560c625e88",
  "after_sha256": "73668cd0ab11b7c6ea1763637371875fd99c611ab859352c648ca27fd7129235",
  "counts": {
    "before": 3,
    "after": 3,
    "added": 1,
    "removed": 1,
    "changed": 1,
    "unchanged": 1
  },
  "changed_cells_by_column": {
    "name": 0,
    "status": 1
  },
  "report_mode": "summary"
}
(stderr empty)
exit status: 1
```

## Equal check

```text
$ python3 csv_change.py examples/before.csv examples/before.csv --key id --check --summary-only
{
  "format_version": 2,
  "tool_version": "0.1.10-preview",
  "before_sha256": "47a72c33f86207715fd3f1784d61f65e5449307dee4fa565d11e54560c625e88",
  "after_sha256": "47a72c33f86207715fd3f1784d61f65e5449307dee4fa565d11e54560c625e88",
  "counts": {
    "before": 3,
    "after": 3,
    "added": 0,
    "removed": 0,
    "changed": 0,
    "unchanged": 3
  },
  "changed_cells_by_column": {
    "name": 0,
    "status": 0
  },
  "report_mode": "summary"
}
(stderr empty)
exit status: 0
```

## Invalid duplicate key

```text
$ python3 csv_change.py examples/before.csv evaluation/duplicate-key.csv --key id --check
(stdout empty)
stderr: {"error": "record 2 repeats a key"}
exit status: 2
```
