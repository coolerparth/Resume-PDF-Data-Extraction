import re
import spacy
from typing import List

from core.schema import (
    ExtractedBlock, ResumeProfile,
    PersonalInfo, LinkItem, ExperienceBlock
)

# Regex patterns
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")

# Common tech skills dictionary for cross-referencing
SKILLS_DICT = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "react", "nextjs", "nodejs", "fastapi", "django", "flask", "spring",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "git",
    "machine learning", "deep learning", "nlp", "computer vision",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "html", "css", "tailwind", "graphql", "rest api", "linux", "bash"
}


class NLPParser:
    """
    Phase 4 — Comprehension.
    Takes the ordered ExtractedBlock list and uses spaCy (RoBERTa transformer)
    for Named Entity Recognition + regex for strict pattern matching.
    Outputs a fully structured ResumeProfile.
    """

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_trf")
        except OSError:
            raise RuntimeError(
                "spaCy model not found. Run: python -m spacy download en_core_web_trf"
            )

    def parse(self, blocks: List[ExtractedBlock]) -> ResumeProfile:
        full_text = "\n".join(b.text for b in blocks if b.text)
        doc = self.nlp(full_text)

        personal_info = self._extract_personal_info(full_text, doc)
        links = self._collect_links(blocks)
        skills = self._extract_skills(full_text)
        experience_blocks = self._extract_experience(blocks, doc)

        return ResumeProfile(
            personal_info=personal_info,
            links=links,
            skills=skills,
            experience_blocks=experience_blocks
        )

    def _extract_personal_info(self, text: str, doc) -> PersonalInfo:
        # Name — first PERSON entity spaCy finds
        name = None
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text
                break

        # Email — regex
        email_match = EMAIL_RE.search(text)
        email = email_match.group(0) if email_match else None

        # Phone — regex
        phone_match = PHONE_RE.search(text)
        phone = phone_match.group(0).strip() if phone_match else None

        return PersonalInfo(name=name, email=email, phone=phone)

    def _collect_links(self, blocks: List[ExtractedBlock]) -> List[LinkItem]:
        """Collect all URLs extracted by pdfplumber across all blocks."""
        links = []
        seen_urls = set()
        for block in blocks:
            for link in block.urls:
                if link.url not in seen_urls:
                    links.append(link)
                    seen_urls.add(link.url)
        return links

    def _extract_skills(self, text: str) -> List[str]:
        """Cross-reference extracted text against the skills dictionary."""
        text_lower = text.lower()
        found = [skill for skill in SKILLS_DICT if skill in text_lower]
        return sorted(found)

    def _extract_experience(
        self, blocks: List[ExtractedBlock], doc
    ) -> List[ExperienceBlock]:
        """
        Identifies experience-related blocks by label and extracts
        company names using spaCy ORG entities per block.
        Labels match docling's actual DocLayNet output vocabulary.
        """
        experience = []

        # Real docling labels that contain body/experience content
        experience_labels = {
            "text", "list_item", "paragraph",
            "caption", "footnote", "formula"
        }

        for block in blocks:
            if block.label.lower() not in experience_labels or not block.text:
                continue

            block_doc = self.nlp(block.text)
            company = None
            for ent in block_doc.ents:
                if ent.label_ == "ORG":
                    company = ent.text
                    break

            experience.append(ExperienceBlock(
                company=company,
                text_content=block.text
            ))

        return experience