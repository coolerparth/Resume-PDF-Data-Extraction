import pdfplumber
from typing import List

from core.schema import BoundingBox, ExtractedBlock, LinkItem
from core.ocr_fallback import OCRFallback


class Extractor:
    """
    Phase 2 — Deep Read & Link Mining.
    Takes the ordered bounding boxes from LayoutMapper and uses pdfplumber
    to crop each box and extract text + hidden URLs from PDF annotations.
    Falls back to OCRFallback if a box yields zero text.
    """

    def __init__(self):
        self.ocr = OCRFallback()

    def extract(self, pdf_path: str, boxes: List[BoundingBox]) -> List[ExtractedBlock]:
        """
        Iterates through every bounding box, crops the PDF to that region,
        extracts text and hyperlinks, triggers OCR if text is empty.
        Returns a list of ExtractedBlock objects in reading order.
        """
        blocks = []

        with pdfplumber.open(pdf_path) as pdf:
            for box in boxes:
                page = pdf.pages[box.page]

                # Crop to the exact bounding box — cannot bleed into adjacent columns
                cropped = page.crop((box.x0, box.y0, box.x1, box.y1))
                text = cropped.extract_text() or ""

                # OCR fallback if pdfplumber finds nothing
                if not text.strip():
                    text = self.ocr.read_box(pdf_path, box)

                # Extract hidden hyperlinks from PDF annotations
                urls = self._extract_urls(page, box)

                blocks.append(ExtractedBlock(
                    label=box.label,
                    text=text.strip(),
                    urls=urls,
                    page=box.page
                ))

        return blocks

    def _extract_urls(self, page, box: BoundingBox) -> List[LinkItem]:
        """
        Checks the page's annotation metadata for any hyperlinks whose
        coordinates fall inside the current bounding box.
        """
        urls = []
        annots = page.annots or []

        for annot in annots:
            uri = annot.get("uri")
            if not uri:
                continue

            ax0, ay0, ax1, ay1 = annot["x0"], annot["y0"], annot["x1"], annot["y1"]

            # Only grab the link if it physically lives inside this box
            if ax0 >= box.x0 and ay0 >= box.y0 and ax1 <= box.x1 and ay1 <= box.y1:
                # Use the annotated text as label, fallback to domain name
                label = self._derive_label(uri)
                urls.append(LinkItem(label=label, url=uri))

        return urls

    def _derive_label(self, url: str) -> str:
        """Derive a human-readable label from a URL if no text label is available."""
        if "github" in url:
            return "GitHub"
        if "linkedin" in url:
            return "LinkedIn"
        if "portfolio" in url or "notion" in url:
            return "Portfolio"
        return url.split("//")[-1].split("/")[0]  # fallback: domain name
