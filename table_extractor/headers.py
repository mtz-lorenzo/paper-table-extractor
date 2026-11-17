"""Multi-level header handling (merged cells) and DataFrame construction."""
import pandas as pd

from .config import MAX_HEADER_ROWS
from .text_utils import is_numeric, unique_headers


def is_section_row(row):
    """Row with only its first cell filled (e.g. 'Somatic'): a category separator."""
    return len(row) > 1 and bool(row[0]) and not any(row[1:])


def count_header_rows(matrix):
    """How many rows at the top form the header. Headers can have 2-3 levels with merged
    cells (e.g. 'Documented in experience' over two subcolumns)."""
    n = 1
    while n < min(MAX_HEADER_ROWS, len(matrix) - 1):
        current, following = matrix[n - 1], matrix[n]
        if any(is_numeric(c) for c in following) or is_section_row(following):
            break
        # (a) an empty cell in the current row that the next row fills -> merged cell
        merged = any(
            current[j] == "" and current[j - 1] != "" and following[j] != ""
            for j in range(1, len(current))
        )
        # (b) continuation row: empty first column and text in the rest
        continuation = following[0] == "" and any(following[1:])
        if not (merged or continuation):
            break
        n += 1
    return n


def flatten_header(rows):
    """Join the header rows into one name per column, repeating titles that span
    several columns to the right."""
    rows = [list(r) for r in rows]
    width = len(rows[0])
    for i in range(len(rows) - 1):      # upper rows
        for j in range(2, width):       # column 0 is the row label: never extended
            if rows[i][j] == "" and rows[i][j - 1] != "" and rows[-1][j] != "":
                rows[i][j] = rows[i][j - 1]

    names = []
    for j in range(width):
        parts = []
        for r in rows:
            if r[j] and r[j] not in parts:
                parts.append(r[j])
        names.append(" – ".join(parts))
    return names


def matrix_to_df(matrix):
    """Convert a matrix (list of lists of str) into a DataFrame."""
    width = max(len(r) for r in matrix)
    matrix = [r + [""] * (width - len(r)) for r in matrix]
    n = count_header_rows(matrix)
    columns = unique_headers(flatten_header(matrix[:n]))
    return pd.DataFrame(matrix[n:], columns=columns)
