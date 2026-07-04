import os
import pathlib
import tempfile
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import AnalyzeRequest
from services.format_checker import detect_format_issues
from services.jd_analyzer import analyze_jd
from services.llm import generate_suggestions
from services.matcher import match_resume
from services.parser import parse_resume

load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

ALLOWED_SUFFIXES = {".pdf", ".docx"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="ATS Resume Scoring API", lifespan=lifespan)

_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if _frontend := os.getenv("FRONTEND_URL"):
    _origins.append(_frontend)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _save_upload(file: UploadFile) -> tuple[pathlib.Path, str]:
    suffix = pathlib.Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400, detail="Unsupported file type. Use PDF or DOCX."
        )
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(content)
    tmp.close()
    return pathlib.Path(tmp.name), suffix


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/parse")
async def parse_endpoint(file: UploadFile = File(...)):
    path, suffix = await _save_upload(file)
    try:
        result = parse_resume(path, suffix)
        return JSONResponse(content=result)
    finally:
        path.unlink(missing_ok=True)


@app.post("/format-check")
async def format_check_endpoint(file: UploadFile = File(...)):
    path, suffix = await _save_upload(file)
    try:
        from services.parser import extract_text

        raw_text = extract_text(path, suffix)
        flags = detect_format_issues(path, suffix, raw_text)
        return JSONResponse(content={"flags": flags})
    finally:
        path.unlink(missing_ok=True)


@app.post("/jd-analyze")
async def jd_analyze_endpoint(jd_text: str = Form(...)):
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text is required.")
    return JSONResponse(content=analyze_jd(jd_text))


@app.post("/analyze")
async def analyze_endpoint(body: AnalyzeRequest):
    result = match_resume(body.resume.model_dump(), body.jd_analysis.model_dump())
    return JSONResponse(content=result)


@app.post("/report")
async def report_endpoint(
    file: UploadFile = File(...),
    jd_text: str = Form(...),
):
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text is required.")

    path, suffix = await _save_upload(file)
    try:
        resume_json = parse_resume(path, suffix)
        format_flags = detect_format_issues(path, suffix, resume_json["raw_text"])
        jd_json = analyze_jd(jd_text)
        analysis = match_resume(resume_json, jd_json)
        analysis["suggestions"] = generate_suggestions(resume_json, jd_json, analysis)
        analysis["format_flags"] = format_flags
        analysis["jd_analysis"] = jd_json
        analysis["resume_sections"] = resume_json["sections"]
        return JSONResponse(content=analysis)
    finally:
        path.unlink(missing_ok=True)
