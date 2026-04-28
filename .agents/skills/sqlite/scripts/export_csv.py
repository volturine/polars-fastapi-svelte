#!/usr/bin/env python3

import csv
import json
import pathlib
import sqlite3
import sys


def main() -> int:
    if len(sys.argv) not in {4, 5}:
        print(f"usage: {sys.argv[0]} <db-path> <sql> <output-csv> [params-json]", file=sys.stderr)
        return 1

    path = pathlib.Path(sys.argv[1]).resolve()
    sql = sys.argv[2]
    out = pathlib.Path(sys.argv[3]).resolve()
    params = json.loads(sys.argv[4]) if len(sys.argv) == 5 else []

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        cols = [item[0] for item in cur.description or []]
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(cols)
            for row in rows:
                writer.writerow([row[col] for col in cols])
        print(f"exported {len(rows)} rows to {out}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
