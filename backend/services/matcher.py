import re


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9+#.\s]", "", text.lower()).strip()


def _token_set(text: str) -> set[str]:
    return {t for t in _normalize(text).split() if len(t) > 1}


def _skill_match(resume_text: str, resume_skills: set[str], jd_skill: str) -> bool:
    norm_skill = _normalize(jd_skill)
    if not norm_skill:
        return False
    if norm_skill in resume_skills:
        return True
    if norm_skill in _normalize(resume_text):
        return True
    skill_tokens = _token_set(jd_skill)
    if skill_tokens and skill_tokens.issubset(_token_set(resume_text)):
        return True
    return False


def _collect_resume_skills(resume: dict) -> set[str]:
    sections = resume.get("sections", {})
    skills = {_normalize(s) for s in sections.get("skills", []) if s}
    for key in ("experience", "education", "projects"):
        for entry in sections.get(key, []):
            for value in entry.values():
                if isinstance(value, str):
                    skills.add(_normalize(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            skills.add(_normalize(item))
    return {s for s in skills if s}


def match_resume(resume: dict, jd_analysis: dict) -> dict:
    resume_text = resume.get("raw_text", "")
    resume_skills = _collect_resume_skills(resume)

    # Aggregate all required and preferred items from the granular JD analysis
    required = (
        jd_analysis.get("required_skills", [])
        + jd_analysis.get("required_concepts", [])
        + jd_analysis.get("required_workflows", [])
        + jd_analysis.get("required_tools", [])
    )
    nice = (
        jd_analysis.get("preferred_skills", [])
        + jd_analysis.get("preferred_concepts", [])
        + jd_analysis.get("preferred_workflows", [])
        + jd_analysis.get("preferred_tools", [])
    )
    keywords = jd_analysis.get("keywords", [])

    matched_required = [s for s in required if _skill_match(resume_text, resume_skills, s)]
    missing_required = [s for s in required if s not in matched_required]
    matched_nice = [s for s in nice if _skill_match(resume_text, resume_skills, s)]
    missing_nice = [s for s in nice if s not in matched_nice]
    matched_keywords = [k for k in keywords if _skill_match(resume_text, resume_skills, k)]

    req_weight = 3
    nice_weight = 1.5
    kw_weight = 0.5

    earned = (
        req_weight * len(matched_required)
        + nice_weight * len(matched_nice)
        + kw_weight * len(matched_keywords)
    )
    possible = (
        req_weight * len(required)
        + nice_weight * len(nice)
        + kw_weight * len(keywords)
    ) or 1

    match_score = min(100, int(round(100 * earned / possible)))

    return {
        "match_score": match_score,
        "missing_required_skills": missing_required,
        "missing_nice_to_have": missing_nice,
        "matched_skills": matched_required + matched_nice,
        "suggestions": [],
    }
