import sqlite3

import pandas as pd

from extractor_tablas.base_datos import columnas_sql, guardar_en_db, nombre_tabla_sql


def _tabla(df, archivo="Paper DMT 2024.pdf", pagina=3, tabla_num=1, titulo="Table 2."):
    return {"archivo": archivo, "pagina": pagina, "tabla_num": tabla_num, "titulo": titulo, "df": df}


def test_nombre_tabla_sql_se_sanea():
    nombre = nombre_tabla_sql(_tabla(pd.DataFrame(), archivo="Paper DMT (2024)-v2.pdf"))
    assert nombre == "paper_dmt_2024_v2__p3_t1"


def test_columnas_sql_desambigua_mayusculas():
    assert columnas_sql(["Mean", "mean", "Mean"]) == ["Mean", "mean_2", "Mean_3"]


def test_guarda_tabla_y_catalogo(tmp_path):
    db = str(tmp_path / "t.db")
    df = pd.DataFrame([["DMT", "127"], ["Psilocin", "49"]], columns=["Compound", "Ki"])
    assert guardar_en_db([_tabla(df)], [0], db) == 1

    con = sqlite3.connect(db)
    filas = con.execute('SELECT * FROM "paper_dmt_2024__p3_t1"').fetchall()
    cat = con.execute("SELECT nombre_sql, archivo, pagina, titulo, filas, columnas FROM catalogo").fetchall()
    con.close()
    assert filas == [("DMT", "127"), ("Psilocin", "49")]
    assert cat == [("paper_dmt_2024__p3_t1", "Paper DMT 2024.pdf", 3, "Table 2.", 2, 2)]


def test_guardar_dos_veces_reemplaza_en_lugar_de_duplicar(tmp_path):
    db = str(tmp_path / "t.db")
    t = _tabla(pd.DataFrame([["a", "1"]], columns=["x", "y"]))
    guardar_en_db([t], [0], db)
    guardar_en_db([t], [0], db)

    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM catalogo").fetchone()[0] == 1
    assert con.execute('SELECT COUNT(*) FROM "paper_dmt_2024__p3_t1"').fetchone()[0] == 1
    con.close()


def test_columnas_que_chocan_por_mayusculas_no_rompen_el_guardado(tmp_path):
    db = str(tmp_path / "t.db")
    t = _tabla(pd.DataFrame([["a", "1"]], columns=["Mean", "mean"]))
    guardar_en_db([t], [0], db)

    con = sqlite3.connect(db)
    columnas = [c[1] for c in con.execute('PRAGMA table_info("paper_dmt_2024__p3_t1")')]
    con.close()
    assert columnas == ["Mean", "mean_2"]
