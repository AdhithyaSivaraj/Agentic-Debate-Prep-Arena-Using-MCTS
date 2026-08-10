# Agentic Debate Arena: Logic-Verified Argument Coaching

> A course project for **Foundations of AI** — multi-unit syllabus integration using
> propositional resolution (Unit IV), MCTS (Unit III), semantic search (Unit II),
> and Knowledge-Based Agent architecture (Units I & IV), wrapped in an agentic LLM
> orchestration layer.

## Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your API keys

# Frontend (Phase 7+)
cd frontend
npm install
npm run dev
```

## Project structure

See `project_structure_prompt.md` in the project root for the full spec.

## Build phases

See `PROJECT_STATE.md` for current progress and handoff protocol.
