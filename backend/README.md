# Agentic Debate Arena — Backend

FastAPI service for the debate arena: propositional resolution (Unit IV), MCTS
rebuttal selection (Unit III), semantic fact retrieval (Unit II) and per-agent
TELL/ASK knowledge bases (Units I & IV), orchestrated by LLM debater agents.

See the [root README](../README.md) for the full overview and the one-command launcher.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` with any of `GROQ_API_KEY`, `GEMINI_API_KEY`, `NVIDIA_API_KEY`,
`OPENROUTER_API_KEY`. With no keys, agents run in deterministic fallback mode
(MCTS and resolution still execute; only phrasing is templated).

## Run

```bash
uvicorn main:app --app-dir app --reload --port 8000
```

## Test

```bash
pytest
```

Tests run offline: `tests/conftest.py` replaces every LLM call with a deterministic fake.
