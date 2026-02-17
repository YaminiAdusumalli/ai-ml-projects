import re
import uuid


SAFE_SPACE_RE = re.compile(r"\s+")


def new_resume_id() -> str:
    return str(uuid.uuid4())[:8]


def normalize_ws(text: str) -> str:
    return SAFE_SPACE_RE.sub(" ", text or "").strip()


SECTION_HEADERS = [
    "summary",
    "objective",
    "experience",
    "work experience",
    "projects",
    "skills",
    "technical skills",
    "education",
    "certifications",
    "awards",
]
