"""Funciones geométricas sobre la página: segmentos de texto, recortes, reglas, títulos."""
from .config import ANCHO_MIN_REGLA, HUECO_SEGMENTO, MAX_DIST_TITULO


def _segmento(palabras):
    return {
        "text": " ".join(w["text"] for w in palabras),
        "x0": min(w["x0"] for w in palabras),
        "x1": max(w["x1"] for w in palabras),
        "top": min(w["top"] for w in palabras),
        "bottom": max(w["bottom"] for w in palabras),
    }


def segmentos_de_texto(pagina):
    """Agrupa las palabras por renglón y corta cada renglón donde haya un hueco grande,
    así un título en la columna derecha no queda pegado al texto de la izquierda."""
    renglones = {}
    for w in pagina.extract_words():
        renglones.setdefault(round(w["top"] / 3), []).append(w)

    segmentos = []
    for palabras in renglones.values():
        palabras.sort(key=lambda w: w["x0"])
        actual = [palabras[0]]
        for w in palabras[1:]:
            if w["x0"] - actual[-1]["x1"] > HUECO_SEGMENTO:
                segmentos.append(_segmento(actual))
                actual = [w]
            else:
                actual.append(w)
        segmentos.append(_segmento(actual))
    return sorted(segmentos, key=lambda s: (s["top"], s["x0"]))


def recortar(pagina, bbox):
    """Recorta la página a bbox (limitado a sus bordes); None si queda demasiado chico."""
    x0, top, x1, bottom = bbox
    x0, x1 = max(0, x0), min(pagina.width, x1)
    top, bottom = max(0, top), min(pagina.height, bottom)
    if x1 - x0 < 20 or bottom - top < 10:
        return None
    return pagina.crop((x0, top, x1, bottom))


def reglas_horizontales(region, ancho_pagina):
    """Líneas horizontales anchas (típicas de tablas estilo 'booktabs': arriba, bajo el
    encabezado y abajo). Devuelve las que tienen el mismo ancho que la primera."""
    reglas = []
    for o in list(region.lines) + list(region.rects):
        alto = abs(o["bottom"] - o["top"])
        ancho = o["x1"] - o["x0"]
        if alto <= 2.5 and ancho >= ANCHO_MIN_REGLA * ancho_pagina:
            reglas.append(o)
    if not reglas:
        return []
    reglas.sort(key=lambda o: o["top"])
    base = reglas[0]
    similares = [
        r for r in reglas
        if abs(r["x0"] - base["x0"]) <= 15 and abs(r["x1"] - base["x1"]) <= 15
    ]
    # Cortar si hay un salto enorme entre reglas (ya es otra cosa)
    resultado = [similares[0]]
    for r in similares[1:]:
        if r["top"] - resultado[-1]["bottom"] > 300:
            break
        resultado.append(r)
    return resultado


def titulo_sobre(bbox, titulos):
    """Texto del título 'Table N' más cercano por encima de la tabla ('' si no hay)."""
    mejor = None
    for t in titulos:
        dist = bbox[1] - t["bottom"]
        if -3 <= dist <= MAX_DIST_TITULO and (mejor is None or t["bottom"] > mejor["bottom"]):
            mejor = t
    return mejor["text"] if mejor else ""


def dentro_de(obj, bbox):
    """True si el objeto (char, línea, etc.) está contenido en bbox."""
    return (
        obj["x0"] >= bbox[0] - 1
        and obj["x1"] <= bbox[2] + 1
        and obj["top"] >= bbox[1] - 1
        and obj["bottom"] <= bbox[3] + 1
    )
