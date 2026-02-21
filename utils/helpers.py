import re
from core.schema import BoundingBox


def clean_text(text: str) -> str:
    """Remove excessive whitespace and non-printable characters from extracted text."""
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)   # strip non-printable
    text = re.sub(r" {2,}", " ", text)               # collapse multiple spaces
    text = re.sub(r"\n{3,}", "\n\n", text)           # collapse excessive newlines
    return text.strip()


def box_contains(outer: BoundingBox, inner: BoundingBox) -> bool:
    """Check if one bounding box fully contains another (same page)."""
    if outer.page != inner.page:
        return False
    return (
        outer.x0 <= inner.x0 and
        outer.y0 <= inner.y0 and
        outer.x1 >= inner.x1 and
        outer.y1 >= inner.y1
    )


def boxes_overlap(a: BoundingBox, b: BoundingBox) -> bool:
    """Check if two bounding boxes overlap at all (same page)."""
    if a.page != b.page:
        return False
    return not (a.x1 < b.x0 or b.x1 < a.x0 or a.y1 < b.y0 or b.y1 < a.y0)


def is_valid_url(url: str) -> bool:
    """Basic check that a string looks like a real URL."""
    return url.startswith(("http://", "https://")) and "." in url
