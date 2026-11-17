import sqlite3

import pandas as pd

from table_extractor.database import save_to_db, sql_columns, sql_table_name


def _table(df, file="Paper DMT 2024.pdf", page=3, table_num=1, caption="Table 2."):
    return {"file": file, "page": page, "table_num": table_num, "caption": caption, "df": df}


def test_sql_table_name_is_sanitized():
    name = sql_table_name(_table(pd.DataFrame(), file="Paper DMT (2024)-v2.pdf"))
    assert name == "paper_dmt_2024_v2__p3_t1"


def test_sql_columns_disambiguates_case_collisions():
    assert sql_columns(["Mean", "mean", "Mean"]) == ["Mean", "mean_2", "Mean_3"]


def test_saves_table_and_catalog(tmp_path):
    db = str(tmp_path / "t.db")
    df = pd.DataFrame([["DMT", "127"], ["Psilocin", "49"]], columns=["Compound", "Ki"])
    assert save_to_db([_table(df)], [0], db) == 1

    con = sqlite3.connect(db)
    rows = con.execute('SELECT * FROM "paper_dmt_2024__p3_t1"').fetchall()
    catalog = con.execute(
        "SELECT sql_name, file, page, caption, n_rows, n_cols FROM catalog"
    ).fetchall()
    con.close()
    assert rows == [("DMT", "127"), ("Psilocin", "49")]
    assert catalog == [("paper_dmt_2024__p3_t1", "Paper DMT 2024.pdf", 3, "Table 2.", 2, 2)]


def test_saving_twice_replaces_instead_of_duplicating(tmp_path):
    db = str(tmp_path / "t.db")
    t = _table(pd.DataFrame([["a", "1"]], columns=["x", "y"]))
    save_to_db([t], [0], db)
    save_to_db([t], [0], db)

    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM catalog").fetchone()[0] == 1
    assert con.execute('SELECT COUNT(*) FROM "paper_dmt_2024__p3_t1"').fetchone()[0] == 1
    con.close()


def test_case_colliding_columns_do_not_break_saving(tmp_path):
    db = str(tmp_path / "t.db")
    t = _table(pd.DataFrame([["a", "1"]], columns=["Mean", "mean"]))
    save_to_db([t], [0], db)

    con = sqlite3.connect(db)
    columns = [c[1] for c in con.execute('PRAGMA table_info("paper_dmt_2024__p3_t1")')]
    con.close()
    assert columns == ["Mean", "mean_2"]


def test_non_latin_file_names_are_supported(tmp_path):
    db = str(tmp_path / "t.db")
    t = _table(pd.DataFrame([["a", "1"]], columns=["x", "y"]), file="論文_결과.pdf")
    save_to_db([t], [0], db)

    con = sqlite3.connect(db)
    name = con.execute("SELECT sql_name FROM catalog").fetchone()[0]
    assert con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] == 1
    con.close()
