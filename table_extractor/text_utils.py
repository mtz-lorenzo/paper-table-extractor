"""Helpers for cleaning and classifying cell text."""
import re

_WORD_RE = re.compile(r"[^\W\d_]{2,}")  # 2 or more consecutive letters

# Han ideographs and kana: written without spaces, so words can't be counted by splitting
_UNSPACED_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
# East Asian wide characters (also Hangul): they take twice the width of a Latin letter
_WIDE_RE = re.compile(r"[\u1100-\u11ff\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")


def clean_cell(cell):
    """Collapse line breaks and repeated spaces; None -> ''."""
    return re.sub(r"\s+", " ", cell).strip() if cell else ""


def is_numeric(cell):
    """True if the cell is mostly numbers (e.g. '0.45 ± 0.03', 'p<0.05', '12.5%').
    Labels such as 'IC50' or '10 mg' don't count: they contain words of 2+ letters."""
    compact = cell.replace(" ", "")
    if not compact or _WORD_RE.search(compact):
        return False
    digits = sum(ch.isdigit() for ch in compact)
    return digits / len(compact) >= 0.5


def count_words(cell):
    """Approximate word count. Space-separated text is split on whitespace; for
    Chinese/Japanese (no spaces) every two characters count as one word."""
    unspaced = len(_UNSPACED_RE.findall(cell))
    rest = _UNSPACED_RE.sub(" ", cell)
    return len(rest.split()) + unspaced // 2


def visual_length(cell):
    """Length where East Asian wide characters count double."""
    return len(cell) + len(_WIDE_RE.findall(cell))


def unique_headers(headers):
    """Replace empty headers with col_N and disambiguate repeated ones."""
    seen, result = {}, []
    for i, col in enumerate(headers):
        name = col or f"col_{i}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        result.append(name)
    return result
