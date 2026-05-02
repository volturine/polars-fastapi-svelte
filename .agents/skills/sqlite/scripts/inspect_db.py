#!/usr/bin/env python3

import pathlib
import sqlite3
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <db-path>", file=sys.stderr)
        return 1

    path = pathlib.Path(sys.argv[1]).resolve()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        print(f"database: {path}")
        print(f"tables: {len(tables)}")
        for row in tables:
            name = row["name"]
            count = conn.execute(f'SELECT COUNT(*) AS n FROM "{name}"').fetchone()["n"]
            print(f"\n[{name}] rows={count}")
            cols = conn.execute(f'PRAGMA table_info("{name}")').fetchall()
            for col in cols:
                print(
                    f"  - {col['name']} {col['type'] or 'TEXT'}"
                    f" notnull={col['notnull']} pk={col['pk']} default={col['dflt_value']}"
                )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
