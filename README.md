# Agentic Debate Arena: Logic-Verified Argument Coaching

An agentic AI system where two independently-modeled debater agents argue a topic using only locally-verified facts, with propositional resolution catching logical contradictions and Monte Carlo Tree Search selecting each side's optimal rebuttal.

## 🚀 Quick Start (Single Command)

Run this single command from the project root to start both the backend and frontend servers:

```bash
./run_app.sh
```

- **Frontend UI**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000) (Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs))

---

## 🧪 Run Tests

To run the backend test suite (219 passing unit & integration tests):

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

---

## 🏗️ Architecture Overview

- **Unit IV Propositional Resolution Engine**: `backend/app/core/resolution.py`
- **Unit III Monte Carlo Tree Search**: `backend/app/core/mcts.py`
- **Unit IV Knowledge-Based Agent**: `backend/app/core/knowledge_base.py`
- **Unit II Semantic Search**: `backend/app/core/retrieval.py`
- **Agent A (Google Gemini 2.0 Flash)**: `backend/app/agents/gemini_agent.py`
- **Agent B (NVIDIA Nemotron 3 Ultra)**: `backend/app/agents/nemotron_agent.py`
- **React Cognitive Arena UI**: `frontend/src/`
