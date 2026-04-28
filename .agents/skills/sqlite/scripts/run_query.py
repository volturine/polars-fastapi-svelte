#!/usr/bin/env python3

import json
import pathlib
import sqlite3
import sys


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        print(f"usage: {sys.argv[0]} <db-path> <sql> [params-json]", file=sys.stderr)
        return 1

    path = pathlib.Path(sys.argv[1]).resolve()
    sql = sys.argv[2]
    params = json.loads(sys.argv[3]) if len(sys.argv) == 4 else []

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        print(json.dumps([dict(row) for row in rows], indent=2, default=str))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
