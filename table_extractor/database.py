"""Save tables to a SQLite database."""
import os
import re
import sqlite3
from datetime import datetime

from .config import DB_PATH


def sql_table_name(table):
    """SQL table name: <pdf>__p<page>_t<n>, using only letters, digits and _."""
    base = re.sub(r"\W+", "_", os.path.splitext(table["file"])[0]).strip("_").lower()
    return f"{base[:40] or 'paper'}__p{table['page']}_t{table['table_num']}"


def sql_columns(columns):
    """SQLite ignores case in column names: 'Mean' and 'mean' would collide."""
    seen, result = {}, []
    for c in columns:
        key = c.lower()
        if key in seen:
            seen[key] += 1
            c = f"{c}_{seen[key]}"
        else:
            seen[key] = 1
        result.append(c)
    return result


def save_to_db(tables, indices, db_path=DB_PATH):
    """Save each table as its own SQL table and register it in the 'catalog' table.
    Saving the same table again replaces it (no duplicates). Returns how many were saved."""
    con = sqlite3.connect(db_path)
    try:
        with con:  # one transaction: either every table is saved or none
            con.execute(
                """CREATE TABLE IF NOT EXISTS catalog (
                       sql_name  TEXT PRIMARY KEY,
                       file      TEXT,
                       page      INTEGER,
                       table_num INTEGER,
                       caption   TEXT,
                       n_rows    INTEGER,
                       n_cols    INTEGER,
                       saved_at  TEXT
                   )"""
            )
            for i in indices:
                t = tables[i]
                df = t["df"].copy()
                df.columns = sql_columns(list(df.columns))
                name = sql_table_name(t)
                df.to_sql(name, con, if_exists="replace", index=False)
                con.execute(
                    "INSERT OR REPLACE INTO catalog VALUES (?,?,?,?,?,?,?,?)",
                    (
                        name, t["file"], t["page"], t["table_num"],
                        t.get("caption", ""), len(df), len(df.columns),
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
    finally:
        con.close()
    return len(indices)
