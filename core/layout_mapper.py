from typing import List

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

from core.schema import BoundingBox


class LayoutMapper:
    """
    Phase 1 — Visual Glance.
    Passes the PDF through docling's DocLayNet model to detect
    all visual sections and return them as ordered bounding boxes.
    """

    def __init__(self):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False           # OCR handled separately by PaddleOCR
        pipeline_options.do_table_structure = True  # TableFormer for tabular sections

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def get_boxes(self, pdf_path: str) -> List[BoundingBox]:
        """
        Converts a PDF and returns an ordered list of BoundingBox objects.
        Each box represents one detected visual section sorted in correct
        human reading order as determined by DocLayNet.
        """
        result = self.converter.convert(pdf_path)
        boxes = []

        # Iterate over every element in the document in reading order
        for element, _level in result.document.iterate_items():
            # Each element carries a list of provenance records (one per page occurrence)
            for prov in getattr(element, "prov", []):
                bbox = prov.bbox
                page_no = prov.page_no - 1  # docling pages are 1-indexed

                if bbox is None:
                    continue

                label = (
                    element.label.value
                    if hasattr(element.label, "value")
                    else str(element.label)
                )

                boxes.append(BoundingBox(
                    label=label,
                    x0=bbox.l,
                    y0=bbox.t,
                    x1=bbox.r,
                    y1=bbox.b,
                    page=page_no
                ))

        return boxes