# AI Resume Screening & Ranking System

A Python CLI that processes a directory of resumes, applies rule-based minimum eligibility, scores eligible candidates using explainable evidence signals, optionally enriches public GitHub profiles, and emits a JSON report. It is designed for the supplied ~50-resume assignment dataset and can also handle DOCX/TXT.

## Requirements
- Python 3.10+
- Network access only for optional GitHub enrichment; GitHub API failures do not stop screening.

## Setup
```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; optional
# cp .env.example .env   # macOS/Linux
```
No API keys are required for the default deterministic scorer. Optional environment variables are documented in `.env.example`.

## Run
From the repository root:
```bash
python main.py --input ./resumes --output ./output/results.json
```
To use structured LLM scoring (requires `OPENAI_API_KEY` in `.env`):
```bash
python main.py --input ./resumes --output ./output/results.json --use-llm
```

To run offline without GitHub requests:
```bash
python main.py --input ./resumes --output ./output/results.json --no-github
```
To run the test suite:
```bash
pytest -q
```

## Output
`results.json` contains `batch_summary`, `ranked_candidates`, `rejected_candidates`, `all_candidates`, and `processing_errors`. Eligible candidates have a 1-based rank, total score, score breakdown, evidence signals, summary, strengths, concerns, penalties, and GitHub enrichment status. Ineligible candidates include explicit rejection reasons. Parsing failures and duplicate file content are tracked separately.

## Eligibility and ranking
A candidate must have both Python evidence and AI/LLM/RAG/agentic evidence to be eligible. JavaScript, Java, React, or Next.js do not disqualify an otherwise eligible candidate. Eligibility is a hard rule and is evaluated before ranking.

The baseline score uses the assignment's weights:
- AI/agentic/RAG project depth: 40
- Python/backend engineering: 30
- Cloud/deployment/full stack: 15
- GitHub activity: 10
- Engineering depth: 5

Evidence in project/work descriptions is preferred to keyword-only skill lists. Signal scores are capped by category. Clearly thin LLM/API wrapper projects can receive a 10-point penalty; weakly evidenced tutorial-style projects can receive a 5-point penalty. The total is clamped to 0–100. GitHub is never an eligibility requirement and an unavailable profile receives zero enrichment points without failing the batch.

## Design Decisions
- **Filtering:** deterministic Python and AI evidence gates run outside the LLM. This keeps the minimum bar predictable and testable. Because resume parsing and keyword evidence can be imperfect, results should be reviewed by a human before consequential hiring decisions.
- **Scoring:** deterministic, capped evidence signals favor demonstrated implementation, retrieval, orchestration, evaluation, backend work, deployment, and engineering practices. Each score includes matched evidence categories. Penalties are explicit and inspectable.
- **LLM usage:** `src/llm_adapter.py` provides an optional OpenAI structured-output adapter with a strict JSON schema and evidence field. Pass `--use-llm` and set `OPENAI_API_KEY` to enable it. If the model call fails, deterministic scoring remains in place and the failure is recorded. Without the flag/key, output is reproducible and requires no paid credentials.
- **GitHub scoring:** a single public GitHub REST API repository-list call estimates public activity over the last 90 days from recently pushed non-fork repositories. Up to five points come from recent pushes and up to five from repository maintenance/relevance. A per-run username cache avoids repeated calls. API failures, rate limits, and missing profiles are recorded and do not abort processing. `GITHUB_TOKEN` is optional and read only from the environment.
- **Reliability:** each file is isolated in its own exception boundary. SHA-256 hashes identify exact duplicate content; unsupported files are ignored; unreadable or image-only PDFs are reported as failures rather than crashing the batch. GitHub calls use timeouts.
- **Privacy and fairness:** output omits full resume text and focuses on job-related evidence. Automated scores are triage signals, not a substitute for human review.

## If I Had More Time
1. Add OCR fallback for scanned/image-only PDFs and improve layout-aware extraction.
2. Add a calibration set with reviewer-labeled examples to measure false-positive/false-negative eligibility decisions and ranking agreement.
3. Add bounded concurrency plus a per-run cache for GitHub and optional LLM results.
4. Add a human-review interface for inspecting cited resume snippets and correcting extraction errors before final decisions.

## Limitations
Heuristic extraction may miss unusual section layouts or mistake incidental keywords for project evidence. GitHub events are only a partial activity signal, and the public API's recent-event window is limited. Review top-ranked and borderline candidates against their source resumes.
