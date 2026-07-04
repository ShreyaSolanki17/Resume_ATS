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
    required_skills: list[str] = Field(default_factory=list, description="Must-have programming languages, libraries, or frameworks.")
    preferred_skills: list[str] = Field(default_factory=list, description="Nice-to-have programming languages, libraries, or frameworks.")
    required_concepts: list[str] = Field(default_factory=list, description="Must-have theoretical knowledge or methodologies.")
    preferred_concepts: list[str] = Field(default_factory=list, description="Nice-to-have theoretical knowledge or methodologies.")
    required_workflows: list[str] = Field(default_factory=list, description="Must-have processes or development practices (e.g., CI/CD, Agile).")
    preferred_workflows: list[str] = Field(default_factory=list, description="Nice-to-have processes or development practices.")
    required_tools: list[str] = Field(default_factory=list, description="Must-have software or platforms (e.g., Git, Docker, Jira).")
    preferred_tools: list[str] = Field(default_factory=list, description="Nice-to-have software or platforms.")
    experience_level: str = Field(default="", description="Required years or level of experience (e.g., '5+ years', 'Senior').")
    keywords: list[str] = Field(default_factory=list, description="Other important domain-specific terms.")


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
