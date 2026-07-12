#!/usr/bin/env python
"""CLI ingestion.

Usage:
  python ingest.py testcase/test_cases.csv --text-cols title,steps,expected,tags \
      --meta-cols id,jira_id,priority,module
"""
import argparse
import sys

from lib.pipeline import ingest_stream


def main():
    parser = argparse.ArgumentParser(description="Ingest a CSV/XLSX of test cases into Qdrant.")
    parser.add_argument("path", help="Path to a .csv or .xlsx file")
    parser.add_argument("--text-cols", required=True, help="Comma-separated columns to embed")
    parser.add_argument("--meta-cols", required=True, help="Comma-separated columns to keep as payload")
    args = parser.parse_args()

    text_cols = [c.strip() for c in args.text_cols.split(",")]
    meta_cols = [c.strip() for c in args.meta_cols.split(",")]

    for event in ingest_stream(args.path, text_cols, meta_cols):
        stage, status, data = event["stage"], event["status"], event["data"]
        if status == "progress":
            sys.stdout.write(f"\r[{stage}] {data.get('done')}/{data.get('total')}")
            sys.stdout.flush()
        else:
            print(f"\n[{stage}] {status}: {data}")

    print("\nDone.")


if __name__ == "__main__":
    main()
