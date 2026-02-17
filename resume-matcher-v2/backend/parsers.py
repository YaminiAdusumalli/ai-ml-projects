from pathlib import Path
from typing import Dict, Any
from .utils import normalize_ws, SECTION_HEADERS
import docx2txt
from pdfminer.high_level import extract_text as pdf_extract


def _from_txt(text: str) -> Dict[str, Any]:
    text = normalize_ws(text)
    lower = text.lower()
    sections = {"raw_text": text, "sections": {}}

    # initialize all known sections
    for h in SECTION_HEADERS:
        sections["sections"][h] = ""

    # simple rule-based splitting by header keywords
    last = "misc"
    sections["sections"][last] = ""

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for ln in lines:
        l = ln.lower()
        matched = None
        for h in SECTION_HEADERS:
            if l.startswith(h + ":") or l == h or h in l[:40]:
                matched = h
                break
        if matched:
            last = matched
            if last not in sections["sections"]:
                sections["sections"][last] = ""
        sections["sections"][last] = (sections["sections"].get(last, "") + "\n" + ln).strip()

    return sections


def parse_file_to_json(fp: Path) -> Dict[str, Any]:
    """Return a JSON-able dict with fields: raw_text, sections{...}."""
    suffix = fp.suffix.lower()
    if suffix == ".pdf":
        text = pdf_extract(str(fp))
        return _from_txt(text)
    elif suffix in (".docx",):
        text = docx2txt.process(str(fp))
        return _from_txt(text)
    elif suffix in (".txt",):
        return _from_txt(fp.read_text(encoding="utf-8", errors="ignore"))
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
