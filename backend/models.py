from pydantic import BaseModel, Field


class FormatFlag(BaseModel):
    issue: str
    severity: str


class ResumeSections(BaseModel):
    contact: dict = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)


class ParsedResume(BaseModel):
    raw_text: str
    sections: ResumeSections


class JDAnalysis(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    years_experience: str = ""
    keywords: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    resume: ParsedResume
    jd_analysis: JDAnalysis


class AnalysisResult(BaseModel):
    match_score: int
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_nice_to_have: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    format_flags: list[FormatFlag] = Field(default_factory=list)
