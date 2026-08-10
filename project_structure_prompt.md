# PROJECT STRUCTURE PROMPT — "Agentic Debate Arena"

Use this prompt to scaffold the full project. Paste as-is into your AI coding assistant (Antigravity, Claude Code, etc.).

---

## PROMPT START

Build the project scaffolding for **"Agentic Debate Arena: Logic-Verified Argument Coaching"** — a full-stack web app (NOT Electron, browser-based only) with a Python backend and React frontend.

### Stack
- **Backend**: Python 3.11+, FastAPI, exposing a REST API
- **Frontend**: React (Vite), Tailwind CSS, shadcn/ui components
- **LLM APIs**: Google Gemini API (function calling) and Nemotron 3 Ultra via OpenRouter (function calling) — both free tier
- **Embeddings**: Nemotron 3 Embed 1B via OpenRouter (for semantic fact retrieval)
- No database required for MVP — in-memory state per debate session is sufficient (a Python dict keyed by debate_id); design it so swapping in a real DB (SQLite/Postgres) later is easy but not built now

### Backend folder structure
```
/backend
  /app
    main.py                     # FastAPI app entrypoint, CORS setup, route registration
    /api
      routes_debate.py          # /start-debate, /next-turn, /transcript/{id}, /mcts-trace/{turn}
    /core
      resolution.py             # propositional resolution algorithm (clause resolution, contradiction detection)
      mcts.py                   # Monte Carlo Tree Search: Node class, selection/expansion/simulation/backpropagation
      knowledge_base.py         # KB agent class: TELL/ASK interface, stores clauses per debater
      retrieval.py              # embedding-based fact retrieval: cosine similarity search over local fact base
      fact_generation.py        # one-time LLM call to generate + normalize the fact base for a topic into propositional clause form
    /agents
      base_agent.py             # abstract Agent class: percept, decide, act loop
      gemini_agent.py           # Agent A implementation using Gemini function calling
      nemotron_agent.py         # Agent B implementation using Nemotron 3 Ultra function calling (via OpenRouter)
    /tools
      tool_schemas.py           # shared OpenAI-function-calling-compatible JSON schemas for: retrieve_relevant_fact, check_contradiction, select_best_rebuttal, generate_claim
      tool_executor.py          # dispatches a tool_call from either LLM to the correct core/ function
    /models
      schemas.py                # Pydantic models: DebateSession, Turn, Claim, ContradictionResult, MCTSTrace
    config.py                   # API keys (from .env), model names, constants
  requirements.txt
  .env.example                  # GEMINI_API_KEY, OPENROUTER_API_KEY placeholders
  README.md
```

### Frontend folder structure
```
/frontend
  /src
    /components
      DebateArena.jsx           # main layout: two agent panels + shared transcript
      AgentPanel.jsx             # one debater's claim stream, KB state indicator
      ClaimCard.jsx               # a single claim, styled by validity state (valid/contradicted)
      ContradictionAlert.jsx      # highlighted proof trace when resolution finds a conflict
      MCTSTracePanel.jsx          # shows candidate rebuttals considered + which was chosen and why
      TopicSetup.jsx               # topic input screen, triggers fact-base generation
      TranscriptLog.jsx           # scrollable full debate history
    /lib
      api.js                      # fetch wrappers for backend REST endpoints
    /styles
      theme.css                   # design tokens (see UI prompt file for full spec)
    App.jsx
    main.jsx
  index.html
  tailwind.config.js
  vite.config.js
  package.json
```

### Core algorithm requirements (must be real implementations, not LLM-prompted shortcuts)
1. **`resolution.py`**: implement propositional clause resolution from scratch — represent clauses as sets of literals (with negation), implement the resolution rule (resolve two clauses on a complementary literal pair), and a refutation loop that adds the negated goal and checks whether the empty clause is derivable. Include a `check_contradiction(kb: list[Clause]) -> ContradictionResult` function that returns which specific clauses conflict (for the UI's proof trace).
2. **`mcts.py`**: implement a real MCTS with a `Node` class (state, parent, children, visit_count, value), and the four phases as separate methods: `select()` (UCB1), `expand()`, `simulate()` (rollout using a heuristic, not full random playout, since branching factor is language-based), `backpropagate()`. Expose `select_best_rebuttal(candidates: list[str], current_state) -> tuple[str, list[RejectedCandidate]]` so the UI can show both the winner and what was rejected.
3. **`retrieval.py`**: embed all facts once (batch call to Nemotron 3 Embed 1B) and cache the vectors; implement `cosine_similarity(a, b)` manually (simple numpy dot product / norms — don't pull in a heavy vector-DB dependency for this scale); expose `retrieve_relevant_fact(query: str, top_k=1)`.
4. **`knowledge_base.py`**: simple `KnowledgeBase` class per agent with `.tell(clause)` and `.ask_contradiction()` (delegates to resolution.py), matching the TELL/ASK knowledge-based-agent pattern from the syllabus.

### Agent loop requirement
Each agent (`gemini_agent.py`, `nemotron_agent.py`) must implement a loop per turn:
1. Call `retrieve_relevant_fact` tool
2. Call `generate_claim` tool (LLM call) using the retrieved fact + debate context
3. `TELL` the claim into its own KB
4. Call `check_contradiction` tool
5. If contradiction found (in self or opponent), or if under attack: call `select_best_rebuttal` tool before next `generate_claim`

Both agents must be wired to the exact same tool schemas in `tool_schemas.py` — no duplicated tool logic between the Gemini and Nemotron agent files; only the LLM call itself differs.

### API endpoints to build
```
POST /start-debate        { topic: str }              → generates fact base, returns debate_id
POST /next-turn            { debate_id: str }           → advances debate by one turn, returns Turn object (claim, speaker, contradiction_result, mcts_trace)
GET  /transcript/{debate_id}                            → full turn history
GET  /mcts-trace/{debate_id}/{turn_number}               → detailed candidates + scores for that turn
```

### Non-goals for MVP (explicitly do not build yet)
- No user authentication
- No persistent database (in-memory only)
- No live web search during debate turns (only the one-time setup fact-generation call touches the LLM for "new" content; everything else uses the local fact base + algorithms)
- No Modes 2/3 (user-in-the-loop coaching, direct user-vs-agent) yet — build Mode 1 (agent vs agent) fully working first

### Deliverable order
1. `resolution.py` + unit tests on hand-crafted contradiction examples (before touching any LLM code)
2. `mcts.py` + unit tests on a toy game tree
3. `retrieval.py` + `fact_generation.py`
4. `knowledge_base.py`
5. `tool_schemas.py` + `tool_executor.py`
6. `gemini_agent.py` and `nemotron_agent.py`
7. FastAPI routes wiring it all together
8. React frontend consuming the API (start with `TopicSetup.jsx` → `DebateArena.jsx` → transcript rendering → contradiction/MCTS visualization panels last)

## PROMPT END
