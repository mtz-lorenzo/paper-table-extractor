"""Guardado de tablas en una base de datos SQLite."""
import os
import re
import sqlite3
from datetime import datetime

from .config import DB_PATH


def nombre_tabla_sql(tabla):
    """Nombre de la tabla SQL: <pdf>__p<página>_t<n>, solo letras, números y _."""
    base = re.sub(r"\W+", "_", os.path.splitext(tabla["archivo"])[0]).strip("_").lower()
    return f"{base[:40] or 'paper'}__p{tabla['pagina']}_t{tabla['tabla_num']}"


def columnas_sql(columnas):
    """SQLite ignora mayúsculas en nombres de columna: 'Mean' y 'mean' chocarían."""
    vistos, resultado = {}, []
    for c in columnas:
        clave = c.lower()
        if clave in vistos:
            vistos[clave] += 1
            c = f"{c}_{vistos[clave]}"
        else:
            vistos[clave] = 1
        resultado.append(c)
    return resultado


def guardar_en_db(tablas, indices, ruta_db=DB_PATH):
    """Guarda cada tabla como una tabla SQL propia y la registra en el 'catalogo'.
    Volver a guardar la misma tabla la reemplaza (no duplica). Devuelve cuántas guardó."""
    con = sqlite3.connect(ruta_db)
    try:
        with con:  # transacción: o se guardan todas o ninguna
            con.execute(
                """CREATE TABLE IF NOT EXISTS catalogo (
                       nombre_sql  TEXT PRIMARY KEY,
                       archivo     TEXT,
                       pagina      INTEGER,
                       tabla_num   INTEGER,
                       titulo      TEXT,
                       filas       INTEGER,
                       columnas    INTEGER,
                       guardada_en TEXT
                   )"""
            )
            for i in indices:
                t = tablas[i]
                df = t["df"].copy()
                df.columns = columnas_sql(list(df.columns))
                nombre = nombre_tabla_sql(t)
                df.to_sql(nombre, con, if_exists="replace", index=False)
                con.execute(
                    "INSERT OR REPLACE INTO catalogo VALUES (?,?,?,?,?,?,?,?)",
                    (
                        nombre, t["archivo"], t["pagina"], t["tabla_num"],
                        t.get("titulo", ""), len(df), len(df.columns),
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
    finally:
        con.close()
    return len(indices)
