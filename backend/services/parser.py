import pathlib
import re

SECTION_PATTERNS = {
    "skills": re.compile(
        r"^(?:skills|technical\s+skills|core\s+competencies|technologies)\s*:?\s*$",
        re.I,
    ),
    "experience": re.compile(
        r"^(?:experience|work\s+experience|professional\s+experience|employment)\s*:?\s*$",
        re.I,
    ),
    "education": re.compile(r"^(?:education|academic\s+background)\s*:?\s*$", re.I),
    "projects": re.compile(
        r"^(?:projects|personal\s+projects|key\s+projects)\s*:?\s*$", re.I
    ),
}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w-]+", re.I)
GITHUB_RE = re.compile(r"github\.com/[\w-]+", re.I)


def extract_text_from_pdf(file_path: pathlib.Path) -> str:
    import fitz

    doc = fitz.open(str(file_path))
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def extract_text_from_docx(file_path: pathlib.Path) -> str:
    import docx

    document = docx.Document(str(file_path))
    return "\n".join(p.text for p in document.paragraphs)


def extract_text(file_path: pathlib.Path, suffix: str) -> str:
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix == ".docx":
        return extract_text_from_docx(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")


def _extract_contact(raw_text: str) -> dict:
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    header = "\n".join(lines[:8])
    contact: dict = {}
    if email := EMAIL_RE.search(header):
        contact["email"] = email.group()
    if phone := PHONE_RE.search(header):
        contact["phone"] = phone.group()
    if linkedin := LINKEDIN_RE.search(header):
        contact["linkedin"] = linkedin.group()
    if github := GITHUB_RE.search(header):
        contact["github"] = github.group()
    if lines:
        contact["name"] = lines[0]
    return contact


def _parse_skills_block(text: str) -> list[str]:
    parts = re.split(r"[,|•·\n;]", text)
    skills = []
    for part in parts:
        cleaned = part.strip(" •·-\t")
        if cleaned and len(cleaned) < 60:
            skills.append(cleaned)
    return skills


def _parse_experience_block(lines: list[str]) -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None
    date_re = re.compile(
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4})\b", re.I
    )

    for line in lines:
        if date_re.search(line) and len(line) < 120:
            if current:
                entries.append(current)
            current = {"title_line": line, "bullets": []}
        elif current is not None:
            if line.startswith(("•", "-", "*", "–")):
                current["bullets"].append(line.lstrip("•-*– ").strip())
            elif not current.get("company") and len(line) < 80:
                current["company"] = line
            else:
                current["bullets"].append(line)
    if current:
        entries.append(current)
    return entries


def _parse_education_block(lines: list[str]) -> list[dict]:
    entries = []
    for line in lines:
        if len(line) > 3:
            entries.append({"line": line})
    return entries


def parse_sections(raw_text: str) -> dict:
    lines = raw_text.splitlines()
    sections: dict = {
        "contact": _extract_contact(raw_text),
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
    }

    current_section: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_section
        if not current_section or not buffer:
            buffer = []
            return
        block = "\n".join(buffer).strip()
        if current_section == "skills":
            sections["skills"] = _parse_skills_block(block)
        elif current_section == "experience":
            sections["experience"] = _parse_experience_block(buffer)
        elif current_section == "education":
            sections["education"] = _parse_education_block(buffer)
        elif current_section == "projects":
            sections["projects"] = [{"line": ln} for ln in buffer if ln.strip()]
        buffer = []

    for line in lines:
        stripped = line.strip()
        matched = next(
            (name for name, pat in SECTION_PATTERNS.items() if pat.match(stripped)),
            None,
        )
        if matched:
            flush()
            current_section = matched
            continue
        if current_section and stripped:
            buffer.append(stripped)

    flush()

    if not sections["skills"]:
        sections["skills"] = _fallback_skills(raw_text)

    return sections


def _fallback_skills(raw_text: str) -> list[str]:
    common = [
        "Python",
        "JavaScript",
        "TypeScript",
        "Java",
        "React",
        "Node.js",
        "FastAPI",
        "Docker",
        "AWS",
        "SQL",
        "PostgreSQL",
        "MongoDB",
        "Git",
        "Kubernetes",
        "LangChain",
        "LangGraph",
        "LLM",
        "Machine Learning",
        "TensorFlow",
        "PyTorch",
    ]
    lower = raw_text.lower()
    return [skill for skill in common if skill.lower() in lower]


def parse_resume(file_path: pathlib.Path, suffix: str) -> dict:
    raw_text = extract_text(file_path, suffix)
    sections = parse_sections(raw_text)
    return {"raw_text": raw_text, "sections": sections}
