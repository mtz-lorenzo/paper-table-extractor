"""Rebuild a table from its words using vertical "rivers" of white space.

Many paper tables have no vertical rules or grid. pdfplumber's text strategy can place a
column boundary in the middle of a word (e.g. 'Ki (nM)' becoming 'Ki (n' | 'M)'). Here,
columns are defined by empty vertical gaps between words and each word is assigned whole.
"""
import math

from .config import MIN_COLUMN_GAP, RIVER_TOLERANCE, ROW_TOLERANCE


def group_lines(words):
    """Group words into text lines by vertical position."""
    lines = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(w["top"] - lines[-1][0]["top"]) <= ROW_TOLERANCE:
            lines[-1].append(w)
        else:
            lines.append([w])
    return lines


def has_multiple_columns(line):
    """True if the line has at least one large horizontal gap between words.
    Single-block lines (merged header, section row like 'Somatic', a paragraph line)
    say nothing about where the columns are."""
    ordered = sorted(line, key=lambda w: w["x0"])
    return any(b["x0"] - a["x1"] > MIN_COLUMN_GAP for a, b in zip(ordered, ordered[1:]))


def column_separators(lines):
    """x positions of the vertical gaps ("rivers") that cut through nearly all the
    'tabular' lines (single-block lines are ignored)."""
    tabular = [ln for ln in lines if has_multiple_columns(ln)]
    if not tabular:
        return []

    words = [w for ln in tabular for w in ln]
    x_min = math.floor(min(w["x0"] for w in words))
    x_max = math.ceil(max(w["x1"] for w in words))

    coverage = [0] * (x_max - x_min + 1)
    for ln in tabular:
        marked = set()
        for w in ln:
            marked.update(range(math.floor(w["x0"]) - x_min, math.ceil(w["x1"]) - x_min + 1))
        for i in marked:
            coverage[i] += 1

    threshold = int(RIVER_TOLERANCE * len(tabular))
    separators, start = [], None
    for i, c in enumerate(coverage + [threshold + 1]):  # sentinel closes the last run
        if c <= threshold:
            if start is None:
                start = i
        elif start is not None:
            if i - start >= MIN_COLUMN_GAP:
                separators.append(x_min + (start + i) / 2)
            start = None
    return separators


def matrix_from_words(region):
    """Matrix (list of lists of str) for the region, or None if no columns are visible.
    Each word goes whole into one column, and a title spanning several columns is kept
    complete in the first one, leaving the others empty (merged cell)."""
    words = region.extract_words()
    if not words:
        return None
    lines = group_lines(words)
    separators = column_separators(lines)
    if not separators:
        return None

    def column(word):
        return sum(word["x0"] >= s for s in separators)

    matrix = []
    for ln in lines:
        ordered = sorted(ln, key=lambda w: w["x0"])
        row = [[] for _ in range(len(separators) + 1)]
        if has_multiple_columns(ln):
            for w in ordered:
                row[column(w)].append(w["text"])
        else:
            # a single block (merged header, section row) goes whole into the column
            # where it starts, even if it crosses other columns' gaps
            row[column(ordered[0])] = [w["text"] for w in ordered]
        matrix.append([" ".join(parts) for parts in row])
    return matrix
