"""Constantes y expresiones regulares de la detección.

Si el extractor deja pasar falsos positivos o se pierde tablas reales, estos
son los umbrales que conviene ajustar.
"""
import re

# --- Validación de tablas -------------------------------------------------
MIN_FILAS = 3             # encabezado + al menos 2 filas de datos
MIN_COLS = 2
MIN_RELLENO = 0.4         # proporción mínima de celdas con contenido
MAX_FILAS_ENCABEZADO = 3  # máximo de filas de un encabezado combinado

# --- Geometría ------------------------------------------------------------
HUECO_SEGMENTO = 12       # pt de hueco horizontal que parte un renglón en 2 columnas
ANCHO_MIN_REGLA = 0.3     # una línea cuenta como "regla de tabla" si mide >= 30% del ancho
MAX_DIST_TITULO = 200     # pt máximos entre el título "Table N" y la tabla
MIN_HUECO_COLUMNA = 6     # pt de espacio en blanco vertical que separa dos columnas
TOLERANCIA_RIO = 0.15     # fracción de renglones que pueden "cruzar" un hueco (títulos combinados)
TOLERANCIA_RENGLON = 3    # pt de diferencia vertical para considerar palabras del mismo renglón

# --- Base de datos --------------------------------------------------------
DB_PATH = "tablas_papers.db"

# --- Configuraciones de pdfplumber ---------------------------------------
CONFIG_GRILLA = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}

CONFIG_TEXTO_RECORTE = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 3,
    "join_tolerance": 3,
    "min_words_vertical": 2,
    "min_words_horizontal": 1,
}

CONFIG_TEXTO_LIBRE = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 4,
}

# --- Títulos --------------------------------------------------------------
# "Table 1." / "Table 1:" / "TABLE II" / "Tabla 3 -" (no matchea "Table 1 shows...")
RE_TITULO_TABLA = re.compile(
    r"^\s*(table|tabla)\s+(S?\d+[A-Za-z]?|[IVXL]+)\s*(?:[.:|\-–—]|$)", re.I
)
# Cualquier título que delimite el final de una tabla
RE_OTRO_TITULO = re.compile(
    r"^\s*(table|tabla|fig(?:ure|\.)?|figura|scheme|chart)\s+(S?\d+|[IVXL]+)\b", re.I
)
