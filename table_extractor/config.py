"""Constants and regular expressions used for table detection.

If the extractor lets false positives through or misses real tables, these are the
thresholds to tune.
"""
import re

# --- Table validation -----------------------------------------------------
MIN_ROWS = 3             # header + at least 2 data rows
MIN_COLS = 2
MIN_FILL_RATIO = 0.4     # minimum share of cells that must have content
MAX_HEADER_ROWS = 3      # maximum rows in a merged (multi-level) header

# --- Geometry -------------------------------------------------------------
SEGMENT_GAP = 12         # pt of horizontal gap that splits a line into two text columns
MIN_RULE_WIDTH_RATIO = 0.3   # a line counts as a "table rule" if it spans >= 30% of page width
MAX_CAPTION_DISTANCE = 200   # max pt between a "Table N" caption and its table
MIN_COLUMN_GAP = 6       # pt of vertical white space that separates two table columns
RIVER_TOLERANCE = 0.15   # share of rows allowed to "cross" a gap (merged headers)
ROW_TOLERANCE = 3        # pt of vertical difference for words to count as the same row

# --- Database -------------------------------------------------------------
DB_PATH = "paper_tables.db"

# --- pdfplumber settings --------------------------------------------------
GRID_SETTINGS = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}

CROP_TEXT_SETTINGS = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 3,
    "join_tolerance": 3,
    "min_words_vertical": 2,
    "min_words_horizontal": 1,
}

FREE_TEXT_SETTINGS = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 4,
}

# --- Captions -------------------------------------------------------------
# Supported keywords: Table (English), Tabla (Spanish), Tabela (Portuguese),
# 表 (Japanese/Chinese), 표 (Korean).
_NUMBER = r"(?:S?\d+[A-Za-z]?|[IVXL]+)"

# Latin keywords need a punctuation mark (or end of line) after the number, so body text
# such as "Table 1 shows..." is not mistaken for a caption. CJK keywords are followed by
# a space or punctuation ("表1　結合親和性", "표 1. 결합"), which separates them from body
# text such as "表1に示す" or "표 1은".
CAPTION_RE = re.compile(
    rf"^\s*(?:"
    rf"(?:table|tabla|tabela)\s+{_NUMBER}\s*(?:[.:|\-–—：]|$)"
    rf"|(?:表|표)\s*{_NUMBER}(?:[\s.:：．。|\-–—]|$)"
    rf")",
    re.I,
)

# Any caption (table or figure) that marks the end of a table region
ANY_CAPTION_RE = re.compile(
    r"^\s*(?:(?:table|tabla|tabela|fig(?:ure|\.)?|figura|scheme|chart)\s+|(?:表|표|図|그림)\s*)"
    r"(?:S?\d+|[IVXL]+)\b",
    re.I,
)
