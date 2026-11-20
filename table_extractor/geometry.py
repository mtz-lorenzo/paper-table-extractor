"""Page geometry helpers: text segments, crops, ruling lines and captions."""
from .config import (
    MAX_CAPTION_DISTANCE,
    MIN_RULE_WIDTH_RATIO,
    MIN_VERTICAL_RULES,
    SEGMENT_GAP,
    WORD_X_TOLERANCE_RATIO,
)


def _segment(words):
    return {
        "text": " ".join(w["text"] for w in words),
        "x0": min(w["x0"] for w in words),
        "x1": max(w["x1"] for w in words),
        "top": min(w["top"] for w in words),
        "bottom": max(w["bottom"] for w in words),
    }


def text_segments(page):
    """Group words by line and split each line wherever there is a large horizontal gap,
    so a caption in the right-hand column is not glued to the left column's text."""
    lines = {}
    for w in page.extract_words(x_tolerance_ratio=WORD_X_TOLERANCE_RATIO):
        lines.setdefault(round(w["top"] / 3), []).append(w)

    segments = []
    for words in lines.values():
        words.sort(key=lambda w: w["x0"])
        current = [words[0]]
        for w in words[1:]:
            if w["x0"] - current[-1]["x1"] > SEGMENT_GAP:
                segments.append(_segment(current))
                current = [w]
            else:
                current.append(w)
        segments.append(_segment(current))
    return sorted(segments, key=lambda s: (s["top"], s["x0"]))


def crop_page(page, bbox):
    """Crop the page to bbox (clamped to its edges); None if the area is too small."""
    x0, top, x1, bottom = bbox
    x0, x1 = max(0, x0), min(page.width, x1)
    top, bottom = max(0, top), min(page.height, bottom)
    if x1 - x0 < 20 or bottom - top < 10:
        return None
    return page.crop((x0, top, x1, bottom))


def _merge_collinear(segments):
    """Join thin segments that sit at the same height into one rule. Some publishers
    draw each table rule as one short stroke per column."""
    groups = {}
    for o in segments:
        groups.setdefault(round(o["top"]), []).append(o)
    return [
        {
            "x0": min(o["x0"] for o in g), "x1": max(o["x1"] for o in g),
            "top": min(o["top"] for o in g), "bottom": max(o["bottom"] for o in g),
        }
        for g in groups.values()
    ]


def horizontal_rules(region, page_width):
    """Wide horizontal lines (typical of 'booktabs' tables: top, under the header, bottom).
    Returns those with the same width as the first one."""
    thin = []
    # publishers such as Nature draw table rules as thin filled paths (curves)
    for o in list(region.lines) + list(region.rects) + list(region.curves):
        if abs(o["bottom"] - o["top"]) <= 2.5:
            thin.append(o)
    rules = [
        r for r in _merge_collinear(thin)
        if r["x1"] - r["x0"] >= MIN_RULE_WIDTH_RATIO * page_width
    ]
    if not rules:
        return []
    rules.sort(key=lambda o: o["top"])
    base = rules[0]
    similar = [
        r for r in rules
        if abs(r["x0"] - base["x0"]) <= 15 and abs(r["x1"] - base["x1"]) <= 15
    ]
    # Stop at a huge jump between rules (it's something else by then)
    result = [similar[0]]
    for r in similar[1:]:
        if r["top"] - result[-1]["bottom"] > 300:
            break
        result.append(r)
    return result


def has_vertical_rules(page, bbox):
    """True if the area has real vertical ruling lines (a true grid). Tables drawn with
    horizontal rules only (booktabs style) have none: their columns are rebuilt from the
    white space between words instead."""
    x0, top, x1, bottom = bbox
    height = bottom - top
    xs = {
        round(e["x0"])
        for e in page.edges
        if e["orientation"] == "v"
        and e["x0"] >= x0 - 2 and e["x1"] <= x1 + 2
        and e["top"] >= top - 2 and e["bottom"] <= bottom + 2
        and e["height"] >= 0.5 * height
    }
    return len(xs) >= MIN_VERTICAL_RULES


def caption_above(bbox, captions):
    """Text of the closest 'Table N' caption above the table ('' if none)."""
    best = None
    for c in captions:
        distance = bbox[1] - c["bottom"]
        if -3 <= distance <= MAX_CAPTION_DISTANCE and (best is None or c["bottom"] > best["bottom"]):
            best = c
    return best["text"] if best else ""


def inside_bbox(obj, bbox):
    """True if the object (char, line, etc.) lies inside bbox."""
    return (
        obj["x0"] >= bbox[0] - 1
        and obj["x1"] <= bbox[2] + 1
        and obj["top"] >= bbox[1] - 1
        and obj["bottom"] <= bbox[3] + 1
    )
