import io
import numpy as np
from PIL import Image

import fitz  # PyMuPDF — for cropping a page region as an image
from paddleocr import PaddleOCR
from core.schema import BoundingBox


class OCRFallback:
    """
    Phase 3 — Squint Test.
    Called only when pdfplumber finds zero text inside a bounding box.
    Crops that exact region as an image and runs PaddleOCR (PP-OCRv4) on it.
    Never OCRs the full page — only the empty boxes that need it.
    """

    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            show_log=False
        )

    def read_box(self, pdf_path: str, box: BoundingBox) -> str:
        """
        Crops the bounding box region from the PDF page as a high-res image
        and returns the OCR-extracted text string.
        """
        doc = fitz.open(pdf_path)
        page = doc[box.page]

        # Scale up 3x for better OCR accuracy on small text
        mat = fitz.Matrix(3, 3)
        clip = fitz.Rect(box.x0, box.y0, box.x1, box.y1)
        pix = page.get_pixmap(matrix=mat, clip=clip)
        img_bytes = pix.tobytes("png")
        doc.close()

        # PaddleOCR requires a numpy RGB array — not raw bytes
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img_array = np.array(img)

        results = self.ocr.ocr(img_array, cls=True)

        if not results or not results[0]:
            return ""

        lines = [word_info[1][0] for line in results for word_info in line]
        return " ".join(lines).strip()