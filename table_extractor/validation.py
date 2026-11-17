"""Heuristics that decide whether a matrix is a real table or running text."""
from .config import MIN_COLS, MIN_FILL_RATIO, MIN_ROWS
from .headers import count_header_rows
from .text_utils import count_words, is_numeric, visual_length


def is_prose_row(row):
    """Row that looks like running text (a paragraph or a long caption), not data."""
    filled = [c for c in row if c]
    if not filled:
        return True
    total = sum(visual_length(c) for c in filled)
    if len(filled) == 1:
        return total >= 45
    no_numbers = not any(is_numeric(c) for c in filled)
    lowercase = sum(c[0].islower() for c in filled) / len(filled)
    return no_numbers and total >= 60 and lowercase >= 0.5


def tidy_matrix(matrix):
    """Drop empty rows/columns and prose rows at the edges (caption, nearby paragraphs)."""
    matrix = [r for r in matrix if any(r)]
    if not matrix:
        return []
    width = max(len(r) for r in matrix)
    matrix = [r + [""] * (width - len(r)) for r in matrix]
    keep = [j for j in range(width) if any(r[j] for r in matrix)]
    matrix = [[r[j] for j in keep] for r in matrix]
    while matrix and is_prose_row(matrix[0]):
        matrix.pop(0)
    while matrix and is_prose_row(matrix[-1]):
        matrix.pop()
    return matrix


def looks_like_table(matrix, source):
    """
    source:
      'grid'     -> detected from drawn ruling lines (strong evidence)
      'caption'  -> found below a "Table N" caption (strong evidence)
      'free'     -> text alignment only (weak evidence, so it must meet stricter criteria)
    """
    if len(matrix) < MIN_ROWS or len(matrix[0]) < MIN_COLS:
        return False

    header_rows = count_header_rows(matrix)
    body = matrix[header_rows:]
    if len(body) < MIN_ROWS - 1:
        return False

    cells = [c for r in body for c in r]
    filled = [c for c in cells if c]
    if not filled or len(filled) / len(cells) < MIN_FILL_RATIO:
        return False

    numeric_ratio = sum(is_numeric(c) for c in filled) / len(filled)
    long_ratio = sum(count_words(c) >= 6 for c in filled) / len(filled)
    text_cells = [c for c in filled if not is_numeric(c)]
    lowercase_ratio = (
        sum(c[0].islower() for c in text_cells) / len(text_cells) if text_cells else 0.0
    )

    # Prose signals: cells with many words, or lowercase-initial fragments
    if long_ratio > 0.25:
        return False
    if lowercase_ratio > 0.4 and numeric_ratio < 0.2:
        return False

    if source == "free":
        return len(matrix[0]) >= 3 and len(matrix) >= 4 and numeric_ratio >= 0.35
    return True
