import json
import os
import re
import pathlib


JD_SCHEMA = {
    "required_skills": [],
    "preferred_skills": [],
    "required_concepts": [],
    "preferred_concepts": [],
    "required_workflows": [],
    "preferred_workflows": [],
    "required_tools": [],
    "preferred_tools": [],
    "experience_level": "",
    "keywords": [],
}

PROMPT_DIR = pathlib.Path(__file__).parent.parent / "prompts"


def analyze_jd(jd_text: str) -> dict:
    prompt = _build_prompt(jd_text)

    # 1. Try Groq first if API key is available
    if os.getenv("GROQ_API_KEY") and os.getenv("GROQ_API_KEY") != "your-groq-api-key-here":
        try:
            return _call_groq(prompt)
        except Exception:  # Broadly catch API, network, or parsing errors
            pass  # Fall through to the next provider

    # 2. Fallback to Gemini if Groq fails or is not configured
    if os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your-gemini-api-key-here":
        try:
            return _call_gemini(prompt)
        except Exception:
            pass  # Fall through to heuristics

    # 3. Final fallback to local heuristics if all LLMs fail
    return _heuristic_extract(jd_text)

def _build_prompt(jd_text: str) -> str:
    prompt_template = (PROMPT_DIR / "jd_analyzer_prompt.txt").read_text()
    return prompt_template.format(jd_text=jd_text)


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
    # This function can raise json.JSONDecodeError, which the caller must handle.
    data = json.loads(text)
    return {
        "required_skills": _as_str_list(data.get("required_skills")),
        "preferred_skills": _as_str_list(data.get("preferred_skills")),
        "required_concepts": _as_str_list(data.get("required_concepts")),
        "preferred_concepts": _as_str_list(data.get("preferred_concepts")),
        "required_workflows": _as_str_list(data.get("required_workflows")),
        "preferred_workflows": _as_str_list(data.get("preferred_workflows")),
        "required_tools": _as_str_list(data.get("required_tools")),
        "preferred_tools": _as_str_list(data.get("preferred_tools")),
        "experience_level": str(data.get("experience_level", "") or ""),
        "keywords": _as_str_list(data.get("keywords")),
    }


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

    experience = ""
    exp_match = re.search(
        r"(\d+\+?\s*(?:-\s*\d+)?\s*years?|senior|lead|junior|entry-level)", jd_text, re.I
    )
    if exp_match:
        experience = exp_match.group(1)

    if not required:
        required = list(dict.fromkeys(skill_pattern.findall(jd_text)))[:8]

    return {
        "required_skills": required,
        "preferred_skills": nice,
        "required_concepts": [],
        "preferred_concepts": [],
        "required_workflows": [],
        "preferred_workflows": [],
        "required_tools": [],
        "preferred_tools": [],
        "experience_level": experience,
        "keywords": list(dict.fromkeys(keywords))[:12],
    }
