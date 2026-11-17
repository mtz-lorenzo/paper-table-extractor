"""Page geometry helpers: text segments, crops, ruling lines and captions."""
from .config import MAX_CAPTION_DISTANCE, MIN_RULE_WIDTH_RATIO, SEGMENT_GAP


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
    for w in page.extract_words():
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


def horizontal_rules(region, page_width):
    """Wide horizontal lines (typical of 'booktabs' tables: top, under the header, bottom).
    Returns those with the same width as the first one."""
    rules = []
    for o in list(region.lines) + list(region.rects):
        height = abs(o["bottom"] - o["top"])
        width = o["x1"] - o["x0"]
        if height <= 2.5 and width >= MIN_RULE_WIDTH_RATIO * page_width:
            rules.append(o)
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
