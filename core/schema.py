from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional


class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class LinkItem(BaseModel):
    label: str
    url: str


class ExperienceBlock(BaseModel):
    company: Optional[str] = None
    text_content: str


class ResumeProfile(BaseModel):
    personal_info: PersonalInfo
    links: List[LinkItem] = []
    skills: List[str] = []
    experience_blocks: List[ExperienceBlock] = []

    @field_validator("skills")
    @classmethod
    def deduplicate_skills(cls, v):
        seen = set()
        return [x for x in v if not (x.lower() in seen or seen.add(x.lower()))]


class BoundingBox(BaseModel):
    """Internal model — not part of the final output.
    Used to pass layout data between layout_mapper and extractor."""
    label: str        # e.g. "Header", "Sidebar", "Body", "Table"
    x0: float
    y0: float
    x1: float
    y1: float
    page: int = 0


class ExtractedBlock(BaseModel):
    """Internal model — raw extracted data per bounding box,
    before NLP parsing. Passed from extractor to nlp_parser."""
    label: str
    text: str
    urls: List[LinkItem] = []
    page: int = 0