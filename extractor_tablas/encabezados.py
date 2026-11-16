"""Manejo de encabezados de varios niveles (celdas combinadas) y armado del DataFrame."""
import pandas as pd

from .config import MAX_FILAS_ENCABEZADO
from .texto import encabezados_unicos, es_numerica


def es_fila_seccion(fila):
    """Fila con solo la primera celda llena (ej: 'Somatic'): separador de categoría."""
    return len(fila) > 1 and bool(fila[0]) and not any(fila[1:])


def contar_filas_encabezado(matriz):
    """Cuántas filas de arriba forman el encabezado (hay encabezados de 2-3 niveles
    con celdas combinadas, ej: 'Documented in experience' sobre dos subcolumnas)."""
    n = 1
    while n < min(MAX_FILAS_ENCABEZADO, len(matriz) - 1):
        actual, siguiente = matriz[n - 1], matriz[n]
        if any(es_numerica(c) for c in siguiente) or es_fila_seccion(siguiente):
            break
        # (a) celda vacía en la fila actual que la siguiente completa -> celda combinada
        combinada = any(
            actual[j] == "" and actual[j - 1] != "" and siguiente[j] != ""
            for j in range(1, len(actual))
        )
        # (b) fila de continuación: primera columna vacía y el resto con texto
        continuacion = siguiente[0] == "" and any(siguiente[1:])
        if not (combinada or continuacion):
            break
        n += 1
    return n


def aplanar_encabezado(filas):
    """Une las filas de encabezado en un nombre por columna, repitiendo hacia la
    derecha los títulos que abarcan varias columnas."""
    filas = [list(f) for f in filas]
    ancho = len(filas[0])
    for i in range(len(filas) - 1):  # filas superiores
        for j in range(2, ancho):    # la col. 0 es la etiqueta de fila: no se extiende
            if filas[i][j] == "" and filas[i][j - 1] != "" and filas[-1][j] != "":
                filas[i][j] = filas[i][j - 1]

    nombres = []
    for j in range(ancho):
        partes = []
        for f in filas:
            if f[j] and f[j] not in partes:
                partes.append(f[j])
        nombres.append(" – ".join(partes))
    return nombres


def matriz_a_df(matriz):
    """Convierte una matriz (lista de listas de str) en un DataFrame."""
    ancho = max(len(f) for f in matriz)
    matriz = [f + [""] * (ancho - len(f)) for f in matriz]
    n = contar_filas_encabezado(matriz)
    columnas = encabezados_unicos(aplanar_encabezado(matriz[:n]))
    return pd.DataFrame(matriz[n:], columns=columnas)
