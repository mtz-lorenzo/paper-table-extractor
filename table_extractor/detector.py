"""Table detection and extraction from a PDF."""
import logging
import os

import pdfplumber

from .columns import matrix_from_words
from .config import (
    ANY_CAPTION_RE,
    CAPTION_RE,
    CROP_TEXT_SETTINGS,
    FREE_TEXT_SETTINGS,
    GRID_SETTINGS,
    MAX_CAPTION_DISTANCE,
)
from .geometry import (
    caption_above,
    crop_page,
    horizontal_rules,
    inside_bbox,
    text_segments,
)
from .headers import matrix_to_df
from .text_utils import clean_cell
from .validation import looks_like_table, tidy_matrix

logger = logging.getLogger(__name__)


def clean_matrix(table):
    return [[clean_cell(c) for c in row] for row in table]


def _grid_tables(page, captions):
    """Tables with drawn ruling lines (strong evidence)."""
    found = []
    try:
        for t in page.find_tables(GRID_SETTINGS):
            matrix = tidy_matrix(clean_matrix(t.extract()))
            if looks_like_table(matrix, "grid"):
                found.append({
                    "bbox": t.bbox, "matrix": matrix, "source": "grid",
                    "caption": caption_above(t.bbox, captions),
                })
    except Exception:
        logger.warning("Grid detection failed on page %s", page.page_number, exc_info=True)
    return found


def _table_below_caption(page, caption, delimiters):
    """Extract the table located below a 'Table N' caption (or None)."""
    y0 = caption["bottom"]
    following = [d["top"] for d in delimiters if d["top"] > caption["top"] + 1]
    y1 = min(following, default=page.height)

    zone = crop_page(page, (0, y0, page.width, y1))
    if zone is None:
        return None

    rules = horizontal_rules(zone, page.width)
    if len(rules) >= 2:  # "booktabs" style: crop exactly between the rules
        bbox = (
            min(r["x0"] for r in rules) - 2,
            rules[0]["top"] - 1,
            max(r["x1"] for r in rules) + 2,
            rules[-1]["bottom"] + 1,
        )
    else:
        x0 = caption["x0"] - 2 if caption["x0"] >= page.width * 0.45 else 0
        bbox = (x0, y0, page.width, y1)

    region = crop_page(page, bbox)
    if region is None:
        return None

    matrix = matrix_from_words(region)
    if matrix is None:  # no clear columns: fall back to pdfplumber's text strategy
        try:
            table = region.extract_table(CROP_TEXT_SETTINGS)
        except Exception:
            logger.warning("Extraction below caption %r failed (page %s)",
                           caption["text"], page.page_number, exc_info=True)
            return None
        if not table:
            return None
        matrix = clean_matrix(table)

    matrix = tidy_matrix(matrix)
    if looks_like_table(matrix, "caption"):
        return {"bbox": bbox, "matrix": matrix, "source": "caption", "caption": caption["text"]}
    return None


def _free_tables(page, already_found):
    """Tables with no caption and no lines, found by text alignment only (weak evidence)."""
    bboxes = [e["bbox"] for e in already_found]
    remaining = page.filter(lambda o: not any(inside_bbox(o, b) for b in bboxes))
    found = []
    try:
        for table in remaining.extract_tables(FREE_TEXT_SETTINGS):
            matrix = tidy_matrix(clean_matrix(table))
            if looks_like_table(matrix, "free"):
                found.append({
                    "bbox": (0, 0, 0, 0), "matrix": matrix,
                    "source": "free", "caption": "",
                })
    except Exception:
        logger.warning("Extended search failed on page %s", page.page_number, exc_info=True)
    return found


def page_tables(page, extended_search=False):
    """Return the tables on a page as dicts {bbox, matrix, source, caption}."""
    segments = text_segments(page)
    captions = [s for s in segments if CAPTION_RE.match(s["text"])]
    delimiters = [s for s in segments if ANY_CAPTION_RE.match(s["text"])]

    # 1) Tables with a drawn grid
    found = _grid_tables(page, captions)

    # 2) Tables anchored to a "Table N" caption (covers booktabs-style tables)
    for caption in captions:
        already_covered = any(
            -5 <= e["bbox"][1] - caption["bottom"] <= MAX_CAPTION_DISTANCE for e in found
        )
        if already_covered:
            continue
        table = _table_below_caption(page, caption, delimiters)
        if table:
            found.append(table)

    # 3) (Optional) tables with no caption and no lines
    if extended_search:
        found += _free_tables(page, found)

    found.sort(key=lambda e: e["bbox"][1])
    return found


def extract_tables(pdf_path, extended_search=False):
    """Extract every table in a PDF. Each table is an independent dict:
    {file, page, table_num, caption, source, df}."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for idx, e in enumerate(page_tables(page, extended_search), start=1):
                tables.append({
                    "file": os.path.basename(pdf_path),
                    "page": page_number,
                    "table_num": idx,
                    "caption": e["caption"],
                    "source": e["source"],
                    "df": matrix_to_df(e["matrix"]),
                })
    logger.info("%s: %d table(s) extracted", os.path.basename(pdf_path), len(tables))
    return tables
