#!/usr/bin/env python3

import pathlib
import sqlite3
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <db-path> <sql-file>", file=sys.stderr)
        return 1

    path = pathlib.Path(sys.argv[1]).resolve()
    sql_file = pathlib.Path(sys.argv[2]).resolve()
    sql = sql_file.read_text(encoding="utf-8")

    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(sql)
        conn.commit()
        print(f"applied SQL from {sql_file} to {path}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
