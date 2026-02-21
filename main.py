import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from core.layout_mapper import LayoutMapper
from core.extractor import Extractor
from core.nlp_parser import NLPParser
from core.schema import ResumeProfile

app = FastAPI(
    title="A.R.I.E.",
    description="Automated Resume Information Extractor — vision-driven, fully local.",
    version="1.0.0"
)

# Load models once at startup — not on every request
layout_mapper = LayoutMapper()
extractor = Extractor()
nlp_parser = NLPParser()


@app.post("/extract", response_model=ResumeProfile)
async def extract_resume(file: UploadFile = File(...)):
    """
    Upload a resume PDF and receive a structured JSON profile.
    Pipeline: docling → pdfplumber → PaddleOCR (fallback) → spaCy → pydantic
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save upload to a temp file — pdfplumber and docling need a file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        boxes = layout_mapper.get_boxes(tmp_path)
        blocks = extractor.extract(tmp_path, boxes)
        profile = nlp_parser.parse(blocks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)  # clean up temp file

    return JSONResponse(content=profile.model_dump())


@app.get("/health")
def health():
    return {"status": "ok"}
