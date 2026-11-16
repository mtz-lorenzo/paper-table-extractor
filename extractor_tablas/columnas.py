"""Reconstrucción de la tabla a partir de las palabras ("ríos" de espacio en blanco).

Muchas tablas de papers no tienen líneas verticales ni grilla. La estrategia de texto
de pdfplumber a veces pone el corte de columna en medio de una palabra (ej: 'Ki (nM)'
queda como 'Ki (n' | 'M)'). Acá, en cambio, las columnas se definen por los huecos
verticales vacíos entre palabras, y cada palabra se asigna entera a una columna.
"""
import math

from .config import MIN_HUECO_COLUMNA, TOLERANCIA_RENGLON, TOLERANCIA_RIO


def agrupar_renglones(palabras):
    """Agrupa las palabras en renglones según su posición vertical."""
    renglones = []
    for w in sorted(palabras, key=lambda w: (w["top"], w["x0"])):
        if renglones and abs(w["top"] - renglones[-1][0]["top"]) <= TOLERANCIA_RENGLON:
            renglones[-1].append(w)
        else:
            renglones.append([w])
    return renglones


def _tiene_varias_columnas(renglon):
    """True si el renglón tiene al menos un hueco horizontal grande entre palabras.
    Los renglones de un solo bloque (título combinado, fila de sección como 'Somatic',
    una línea de párrafo) no sirven para decidir dónde están las columnas."""
    ordenadas = sorted(renglon, key=lambda w: w["x0"])
    return any(
        b["x0"] - a["x1"] > MIN_HUECO_COLUMNA for a, b in zip(ordenadas, ordenadas[1:])
    )


def separadores_de_columna(renglones):
    """Posiciones x de los huecos verticales (ríos) que atraviesan casi todos los
    renglones 'tabulares' (los de un solo bloque de texto se ignoran)."""
    tabulares = [r for r in renglones if _tiene_varias_columnas(r)]
    if not tabulares:
        return []

    palabras = [w for r in tabulares for w in r]
    x_min = math.floor(min(w["x0"] for w in palabras))
    x_max = math.ceil(max(w["x1"] for w in palabras))

    cobertura = [0] * (x_max - x_min + 1)
    for r in tabulares:
        marcados = set()
        for w in r:
            marcados.update(range(math.floor(w["x0"]) - x_min, math.ceil(w["x1"]) - x_min + 1))
        for i in marcados:
            cobertura[i] += 1

    umbral = int(TOLERANCIA_RIO * len(tabulares))
    separadores, inicio = [], None
    for i, c in enumerate(cobertura + [umbral + 1]):  # centinela para cerrar la última corrida
        if c <= umbral:
            if inicio is None:
                inicio = i
        elif inicio is not None:
            if i - inicio >= MIN_HUECO_COLUMNA:
                separadores.append(x_min + (inicio + i) / 2)
            inicio = None
    return separadores


def matriz_por_palabras(recorte):
    """Matriz (lista de listas de str) de la región, o None si no se distinguen columnas.
    Cada palabra va entera a una columna, y un título que abarca varias columnas queda
    completo en la primera y deja vacías las demás (celda combinada)."""
    palabras = recorte.extract_words()
    if not palabras:
        return None
    renglones = agrupar_renglones(palabras)
    separadores = separadores_de_columna(renglones)
    if not separadores:
        return None

    def columna(palabra):
        return sum(palabra["x0"] >= s for s in separadores)

    matriz = []
    for r in renglones:
        ordenadas = sorted(r, key=lambda w: w["x0"])
        fila = [[] for _ in range(len(separadores) + 1)]
        if _tiene_varias_columnas(r):
            for w in ordenadas:
                fila[columna(w)].append(w["text"])
        else:
            # un solo bloque (título combinado, fila de sección): va entero a la
            # columna donde empieza, aunque cruce el hueco de otras columnas
            fila[columna(ordenadas[0])] = [w["text"] for w in ordenadas]
        matriz.append([" ".join(partes) for partes in fila])
    return matriz
