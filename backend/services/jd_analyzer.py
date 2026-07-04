import json
import os
import re


JD_SCHEMA = {
    "required_skills": [],
    "nice_to_have_skills": [],
    "years_experience": "",
    "keywords": [],
}


def analyze_jd(jd_text: str) -> dict:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    prompt = _build_prompt(jd_text)

    if provider == "gemini" and os.getenv("GEMINI_API_KEY"):
        return _call_gemini(prompt)
    if os.getenv("GROQ_API_KEY") and os.getenv("GROQ_API_KEY") != "your-groq-api-key-here":
        return _call_groq(prompt)
    return _heuristic_extract(jd_text)


def _build_prompt(jd_text: str) -> str:
    return f"""Extract job requirements from this job description.
Return ONLY valid JSON with these fields:
- required_skills: list of must-have technical skills
- nice_to_have_skills: list of preferred but optional skills
- years_experience: string like "3-5 years" or ""
- keywords: list of important domain terms and tools mentioned

Job description:
{jd_text}
"""


def _call_groq(prompt: str) -> dict:
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {
                "role": "system",
                "content": "You extract structured hiring requirements. Respond with JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return _parse_json_response(response.choices[0].message.content or "{}")


def _call_gemini(prompt: str) -> dict:
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    return _parse_json_response(response.text or "{}")


def _parse_json_response(text: str) -> dict:
    try:
        data = json.loads(text)
        return {
            "required_skills": _as_str_list(data.get("required_skills")),
            "nice_to_have_skills": _as_str_list(data.get("nice_to_have_skills")),
            "years_experience": str(data.get("years_experience", "") or ""),
            "keywords": _as_str_list(data.get("keywords")),
        }
    except json.JSONDecodeError:
        return _heuristic_extract(text)


def _as_str_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value).strip()]


def _heuristic_extract(jd_text: str) -> dict:
    lines = jd_text.splitlines()
    required: list[str] = []
    nice: list[str] = []
    keywords: list[str] = []
    in_required = False
    in_nice = False

    skill_pattern = re.compile(
        r"\b(?:Python|JavaScript|TypeScript|Java|React|Node\.?js|FastAPI|Docker|"
        r"AWS|Azure|GCP|SQL|PostgreSQL|MongoDB|Git|Kubernetes|LangChain|LangGraph|"
        r"LLM|Machine Learning|TensorFlow|PyTorch|CI/CD|REST|GraphQL|Redis|Kafka|"
        r"Spark|Hadoop|Terraform|Ansible|Agile|Scrum)\b",
        re.I,
    )

    for line in lines:
        lower = line.lower()
        if re.search(r"required|must have|requirements", lower):
            in_required, in_nice = True, False
        elif re.search(r"nice to have|preferred|bonus", lower):
            in_nice, in_required = True, False
        elif re.search(r"^#{1,3}\s|^\*\*", line):
            in_required = in_nice = False

        for match in skill_pattern.finditer(line):
            skill = match.group()
            bucket = nice if in_nice else required if in_required else keywords
            if skill not in bucket:
                bucket.append(skill)

    years = ""
    years_match = re.search(r"(\d+\+?\s*(?:-\s*\d+)?\s*years?)", jd_text, re.I)
    if years_match:
        years = years_match.group(1)

    if not required:
        required = list(dict.fromkeys(skill_pattern.findall(jd_text)))[:8]

    return {
        "required_skills": required,
        "nice_to_have_skills": nice,
        "years_experience": years,
        "keywords": list(dict.fromkeys(keywords))[:12],
    }
