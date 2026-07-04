import pathlib
import re

STANDARD_HEADERS = [
    "experience",
    "education",
    "skills",
    "projects",
    "summary",
    "contact",
]


def detect_format_issues(file_path: pathlib.Path, suffix: str, raw_text: str = "") -> list[dict]:
    flags: list[dict] = []

    if suffix == ".pdf":
        flags.extend(_check_pdf_layout(file_path))
    else:
        flags.extend(_check_docx_layout(file_path))

    flags.extend(_check_section_headers(raw_text))
    return flags


def _check_pdf_layout(file_path: pathlib.Path) -> list[dict]:
    import fitz

    flags: list[dict] = []
    doc = fitz.open(str(file_path))
    for page in doc:
        blocks = page.get_text("blocks")
        page_width = page.rect.width
        left = any(b[0] < page_width / 3 for b in blocks)
        right = any(b[0] > 2 * page_width / 3 for b in blocks)
        if left and right:
            flags.append(
                {"issue": "multi-column layout detected", "severity": "high"}
            )
            break
        if any(b[6] == 5 for b in blocks):
            flags.append(
                {"issue": "table used for experience section", "severity": "high"}
            )
            break
        if page.get_images():
            flags.append(
                {
                    "issue": "embedded image/icon detected (ATS may skip content)",
                    "severity": "medium",
                }
            )
            break
    doc.close()
    return flags


def _check_docx_layout(file_path: pathlib.Path) -> list[dict]:
    import zipfile

    flags: list[dict] = []
    with zipfile.ZipFile(file_path) as docx_zip:
        for name in docx_zip.namelist():
            if not name.startswith("word/"):
                continue
            content = docx_zip.read(name).decode("utf-8", errors="ignore")
            if "<w:tbl>" in content:
                flags.append(
                    {"issue": "table used in resume", "severity": "high"}
                )
                break
    return flags


def _check_section_headers(raw_text: str) -> list[dict]:
    flags: list[dict] = []
    if not raw_text:
        return flags

    lower = raw_text.lower()
    for header in ("experience", "education", "skills"):
        if not re.search(rf"\b{header}\b", lower):
            flags.append(
                {
                    "issue": f"missing standard section header: '{header.title()}'",
                    "severity": "medium",
                }
            )
    return flags
