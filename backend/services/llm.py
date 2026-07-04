import json
import os
import pathlib


PROMPT_DIR = pathlib.Path(__file__).parent.parent / "prompts"

def generate_suggestions(resume: dict, jd_analysis: dict, match_result: dict) -> list[str]:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    prompt = _build_prompt(resume, jd_analysis, match_result)

    if provider == "gemini" and os.getenv("GEMINI_API_KEY"):
        return _call_gemini(prompt)
    if os.getenv("GROQ_API_KEY") and os.getenv("GROQ_API_KEY") != "your-groq-api-key-here":
        return _call_groq(prompt)
    return _fallback_suggestions(match_result)


def _build_prompt(resume: dict, jd_analysis: dict, match_result: dict) -> str:
    prompt_template = (PROMPT_DIR / "suggestions_prompt.txt").read_text()
    return prompt_template.format(
        jd_analysis=json.dumps(jd_analysis, indent=2),
        match_result=json.dumps(
            {k: v for k, v in match_result.items() if k != "suggestions"}, indent=2
        ),
        resume_excerpt=resume.get("raw_text", "")[:3000],
    )


def _call_groq(prompt: str) -> list[str]:
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {
                "role": "system",
                "content": "You give concise resume improvement advice. Respond with JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return _parse_suggestions(response.choices[0].message.content or "{}")


def _call_gemini(prompt: str) -> list[str]:
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    return _parse_suggestions(response.text or "{}")


def _parse_suggestions(text: str) -> list[str]:
    try:
        data = json.loads(text)
        items = data.get("suggestions", [])
        if isinstance(items, list):
            return [str(s).strip() for s in items if str(s).strip()]
    except json.JSONDecodeError:
        pass
    return []


def _fallback_suggestions(match_result: dict) -> list[str]:
    suggestions = []
    for skill in match_result.get("missing_required_skills", []):
        suggestions.append(
            f"Add '{skill}' explicitly in your Skills or Experience section — it's required in the JD."
        )
    for skill in match_result.get("missing_nice_to_have", []):
        suggestions.append(
            f"Consider adding '{skill}' if you have relevant experience — it's listed as nice-to-have."
        )
    if not suggestions:
        suggestions.append(
            "Strong keyword overlap. Quantify impact in bullet points with metrics (%, $, time saved)."
        )
    return suggestions
