
import re

PYTHON = re.compile(r"\bpython\b", re.IGNORECASE)

AI_PROJECT = re.compile(
    r"\b(?:"
    r"langchain|langgraph|llamaindex|llama.?index|google adk|"
    r"rag|retrieval[ -]augmented generation|"
    r"vector (?:database|search|store)|"
    r"embeddings?|tool[ -]calling|function calling|"
    r"multi[ -]agent|agentic workflow|"
    r"llms?|large language models?|generative ai|"
    r"prompt engineering|prompt evaluation|"
    r"semantic search|transformers?|"
    r"openai api|anthropic api|hugging ?face|"
    r"question answering|text generation|"
    r"document retrieval|ai assistant|"
    r"voice agent|speech recognition"
    r")\b",
    re.IGNORECASE,
)

IMPLEMENTATION = re.compile(
    r"\b(?:built|build|implemented|developed|designed|"
    r"integrated|deployed|engineered|created|trained|"
    r"evaluated|configured|fine[- ]tuned|"
    r"used|using|implemented|automated|processed|"
    r"orchestrated|connected|generated|retrieved|"
    r"served|optimized|established|launched|"
    r"powered|enabled|converted|managed)\b",
    re.IGNORECASE,
)


def check_eligibility(candidate):
    full_text = candidate.get("text") or ""
    project_text = candidate.get("project_evidence_text") or ""

    # Python may be evidenced by the resume's skills section.
    python_found = bool(PYTHON.search(full_text))

    # AI experience must be evidenced in project/work content,
    # not merely by listing AI tools in the skills section.
    ai_found = bool(AI_PROJECT.search(project_text))
    implementation_found = bool(
        IMPLEMENTATION.search(project_text)
    )

    reasons = []

    if not python_found:
        reasons.append("No Python evidence in resume")

    if not project_text.strip():
        reasons.append("No project or work evidence extracted")

    if project_text.strip() and not ai_found:
        reasons.append("No AI/LLM/RAG evidence in project/work section")

    if ai_found and not implementation_found:
        reasons.append("AI evidence found but implementation needs review")

    # Keep candidates with AI evidence but uncertain implementation
    # visible for human review rather than silently discarding them.
    eligible = (
        python_found
        and bool(project_text.strip())
        and ai_found
    )

    candidate["eligible"] = eligible
    candidate["rejection_reasons"] = reasons
    candidate["eligibility_evidence"] = {
        "python_keyword_present": python_found,
        "ai_keyword_present_in_project_or_work_evidence": ai_found,
        "implementation_verb_present": implementation_found,
        "implementation_review_recommended": ai_found and not implementation_found,
        "note": (
            "Automated screening is evidence-based and keyword-assisted. "
            "Review project descriptions before making a hiring decision."
        ),
    }

    return candidate