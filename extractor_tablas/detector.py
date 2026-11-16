"""Detección y extracción de tablas de un PDF."""
import logging
import os

import pdfplumber

from .config import (
    CONFIG_GRILLA,
    CONFIG_TEXTO_LIBRE,
    CONFIG_TEXTO_RECORTE,
    MAX_DIST_TITULO,
    RE_OTRO_TITULO,
    RE_TITULO_TABLA,
)
from .columnas import matriz_por_palabras
from .encabezados import matriz_a_df
from .geometria import (
    dentro_de,
    recortar,
    reglas_horizontales,
    segmentos_de_texto,
    titulo_sobre,
)
from .texto import limpiar_celda
from .validacion import depurar, parece_tabla

logger = logging.getLogger(__name__)


def limpiar_matriz(tabla):
    return [[limpiar_celda(c) for c in fila] for fila in tabla]


def _tablas_con_grilla(pagina, titulos):
    """Tablas con líneas dibujadas (evidencia fuerte)."""
    encontradas = []
    try:
        for t in pagina.find_tables(CONFIG_GRILLA):
            matriz = depurar(limpiar_matriz(t.extract()))
            if parece_tabla(matriz, "grilla"):
                encontradas.append({
                    "bbox": t.bbox, "matriz": matriz, "origen": "grilla",
                    "titulo": titulo_sobre(t.bbox, titulos),
                })
    except Exception:
        logger.warning("Falló la detección por grilla en la página %s",
                       pagina.page_number, exc_info=True)
    return encontradas


def _tabla_bajo_titulo(pagina, titulo, delimitadores):
    """Extrae la tabla ubicada debajo de un título 'Table N' (o None)."""
    y0 = titulo["bottom"]
    siguientes = [d["top"] for d in delimitadores if d["top"] > titulo["top"] + 1]
    y1 = min(siguientes, default=pagina.height)

    zona = recortar(pagina, (0, y0, pagina.width, y1))
    if zona is None:
        return None

    reglas = reglas_horizontales(zona, pagina.width)
    if len(reglas) >= 2:  # estilo "booktabs": recortar exactamente entre las reglas
        bbox = (
            min(r["x0"] for r in reglas) - 2,
            reglas[0]["top"] - 1,
            max(r["x1"] for r in reglas) + 2,
            reglas[-1]["bottom"] + 1,
        )
    else:
        x0 = titulo["x0"] - 2 if titulo["x0"] >= pagina.width * 0.45 else 0
        bbox = (x0, y0, pagina.width, y1)

    recorte = recortar(pagina, bbox)
    if recorte is None:
        return None
    matriz = matriz_por_palabras(recorte)
    if matriz is None:  # sin columnas claras: respaldo con la estrategia de texto de pdfplumber
        try:
            tabla = recorte.extract_table(CONFIG_TEXTO_RECORTE)
        except Exception:
            logger.warning("Falló la extracción bajo el título %r (página %s)",
                           titulo["text"], pagina.page_number, exc_info=True)
            return None
        if not tabla:
            return None
        matriz = limpiar_matriz(tabla)

    matriz = depurar(matriz)
    if parece_tabla(matriz, "titulo"):
        return {"bbox": bbox, "matriz": matriz, "origen": "titulo", "titulo": titulo["text"]}
    return None


def _tablas_libres(pagina, ya_encontradas):
    """Tablas sin título ni líneas, solo por alineación de texto (evidencia débil)."""
    bboxes = [e["bbox"] for e in ya_encontradas]
    restante = pagina.filter(lambda o: not any(dentro_de(o, b) for b in bboxes))
    encontradas = []
    try:
        for tabla in restante.extract_tables(CONFIG_TEXTO_LIBRE):
            matriz = depurar(limpiar_matriz(tabla))
            if parece_tabla(matriz, "libre"):
                encontradas.append({
                    "bbox": (0, 0, 0, 0), "matriz": matriz,
                    "origen": "libre", "titulo": "",
                })
    except Exception:
        logger.warning("Falló la búsqueda ampliada en la página %s",
                       pagina.page_number, exc_info=True)
    return encontradas


def tablas_de_pagina(pagina, permisivo=False):
    """Devuelve las tablas de una página como dicts {bbox, matriz, origen, titulo}."""
    segmentos = segmentos_de_texto(pagina)
    titulos = [s for s in segmentos if RE_TITULO_TABLA.match(s["text"])]
    delimitadores = [s for s in segmentos if RE_OTRO_TITULO.match(s["text"])]

    # 1) Tablas con grilla dibujada
    encontradas = _tablas_con_grilla(pagina, titulos)

    # 2) Tablas ancladas a un título "Table N" (cubre las de estilo booktabs)
    for titulo in titulos:
        ya_cubierto = any(
            -5 <= e["bbox"][1] - titulo["bottom"] <= MAX_DIST_TITULO for e in encontradas
        )
        if ya_cubierto:
            continue
        tabla = _tabla_bajo_titulo(pagina, titulo, delimitadores)
        if tabla:
            encontradas.append(tabla)

    # 3) (Opcional) tablas sin título ni líneas
    if permisivo:
        encontradas += _tablas_libres(pagina, encontradas)

    encontradas.sort(key=lambda e: e["bbox"][1])
    return encontradas


def extraer_tablas(ruta_pdf, permisivo=False):
    """Extrae todas las tablas de un PDF. Cada tabla es un dict independiente:
    {archivo, pagina, tabla_num, titulo, origen, df}."""
    tablas = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages, start=1):
            for idx, e in enumerate(tablas_de_pagina(pagina, permisivo), start=1):
                tablas.append({
                    "archivo": os.path.basename(ruta_pdf),
                    "pagina": num_pagina,
                    "tabla_num": idx,
                    "titulo": e["titulo"],
                    "origen": e["origen"],
                    "df": matriz_a_df(e["matriz"]),
                })
    logger.info("%s: %d tabla(s) extraída(s)", os.path.basename(ruta_pdf), len(tablas))
    return tablas
