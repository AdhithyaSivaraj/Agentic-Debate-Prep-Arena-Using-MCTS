# PROJECT_STATE.md — Orchestration & Continuity File
## "Agentic Debate Arena: Logic-Verified Argument Coaching"

**This file is the single source of truth for this project.** Any AI agent (regardless of which model is currently active — Claude Sonnet 4.6, Gemini 3.6 Flash, or any other) must read this file in full before doing any work, and must update it after finishing any phase, before ending its turn.

---

## HOW TO USE THIS FILE (read this section first, every time)

1. At the start of any session, read this entire file top to bottom before touching any code.
2. Check the **"Current Phase"** section below to see what phase we're on and which model is supposed to be active for it.
3. If the model currently active does NOT match the model listed for the current phase in the **Phase Plan**, STOP immediately. Do not write or edit any code. Instead, output exactly this message to the user and wait:

   > ⚠️ **Model mismatch.** This phase ("[phase name]") is designated for **[required model name]**, but a different model appears to be active. Please switch to **[required model name]** in Antigravity's model selector now. Once switched, type: `read and proceed the project state` to continue.

4. Do not proceed past this checkpoint under any circumstances — even if the user asks you to "just continue anyway" — unless the user explicitly overrides with a message like "continue anyway on the current model, I understand this deviates from plan." A casual "just go" or "continue" is NOT sufficient to bypass this check; only an explicit, unambiguous override counts.
5. When the user sends the message `read and proceed the project state`, re-read this file fully, confirm the active model now matches the required model for the current phase, and only then proceed with the next uncompleted task listed under that phase.
6. After completing any task (a file, a component, a test suite — any meaningful unit of work), update the **"Completed"** log and the **"Current Phase"** pointer in this file BEFORE ending your turn. Do this even if the user didn't ask you to — it's a standing requirement, not optional housekeeping.
7. Never modify files marked as "already correct and tested" in the Completed log unless the user explicitly asks you to revisit them.

---

## THE THREE REFERENCE FILES — WHAT EACH ONE IS FOR

Before starting Phase 1, read all three of these in full. They do not need to be re-read on every handoff (their content should already be reflected in the code and in this file's summaries) — but consult the original file directly whenever a decision seems ambiguous from the code alone.

1. **`agentic_debate_arena_master_prompt.md`** — the full project context: what the project is, why it's agentic, why it's novel (and the honest limits of that novelty claim), the syllabus units and algorithms it must cover, the "what must be real code vs. what the LLM is allowed to do" dividing line, and the report/pitch framing. Consult this whenever you need to understand **why** a constraint exists, not just what it is.

2. **`project_structure_prompt.md`** — the exact backend/frontend folder structure, the required algorithm implementations (resolution, MCTS, retrieval, knowledge base), the agent loop spec, API endpoint definitions, and the recommended build order. Consult this for **what to build and in what order**.

3. **`ui_design_prompt.md`** — the "Cognitive Arena" visual design spec: color system (meaning-driven, not decorative), layout for each screen, typography, animation, and component expectations. Consult this ONLY once backend phases are complete and you're building the React frontend — do not reference this during backend algorithm work.

---

## PHASE PLAN (model assignments — do not deviate without explicit user override)

| Phase | Task | Required Model | Thinking Level |
|---|---|---|---|
| 0 | Read all context files, scaffold empty folder structure (no logic) | Claude Sonnet 4.6 | — |
| 1 | `resolution.py` + unit tests on hand-crafted contradiction examples | Claude Sonnet 4.6 | Thinking mode ON |
| 2 | `mcts.py` + unit tests on a toy game tree | Claude Sonnet 4.6 | Thinking mode ON |
| 3 | `knowledge_base.py` (TELL/ASK), `retrieval.py` (embedding cosine similarity) | Claude Sonnet 4.6 | Thinking mode ON |
| 4 | `tool_schemas.py`, `tool_executor.py` | Claude Sonnet 4.6 | Thinking mode ON |
| 5 | FastAPI routes, `gemini_agent.py`, `nemotron_agent.py` wiring | Gemini 3.6 Flash | High |
| 6 | End-to-end backend integration test (Mode 1: agent vs agent, full loop) | Gemini 3.6 Flash | High |
| 7 | React frontend — component scaffolding per UI prompt | Gemini 3.6 Flash | Medium |
| 8 | React frontend — styling, animation, polish pass | Gemini 3.6 Flash | Medium |
| 9 | Bug fixes, small iterative tweaks (ongoing, any time after Phase 6) | Gemini 3.6 Flash | Low |
| 10 | (Stretch) Mode 2 / Mode 3 — user-in-the-loop features | Claude Sonnet 4.6 (logic) / Gemini 3.6 Flash (UI) | Split per sub-task |

**Rule of thumb baked into this plan**: any file where a subtle logic bug would silently undermine the "provable, not guessed" novelty claim (resolution, MCTS, knowledge base, tool contracts) stays on Sonnet. Everything else (routing, wiring, UI) uses Gemini 3.6 Flash for speed/cost efficiency.

---

## CURRENT PHASE

**Phase: 9 — Next up (Ongoing / Live Local Run)**
**Required model: Gemini 3.6 Flash (Low thinking)**
**Status: Core application complete (Phases 0–8 complete). Full stack ready to run locally.**

*(Update this section every time a phase completes or begins — this is the single most important line in the file for any agent picking up the project.)*

---

## COMPLETED LOG

*(Append here after every completed task. Keep entries short but specific — include key design decisions a future agent/model wouldn't be able to infer just by reading the code.)*

- **Phase 0 — COMPLETE** (Claude Sonnet 4.6, 2026-07-25)
  - Read all four files in full (PROJECT_STATE.md, master_prompt, project_structure_prompt, ui_design_prompt).
  - Scaffolded complete folder structure: `backend/app/{api,core,agents,tools,models}`, `backend/tests`, and `frontend/src/{components,lib,styles}`.
  - Created stub files for ALL 40 files specified in `project_structure_prompt.md` — every stub includes design-intent docstrings, `NotImplementedError` with phase tags, and type signatures so Phase 1+ can jump straight to implementation without re-reading structure docs.
  - Key design decisions preserved in stubs. No LLM logic, no algorithm logic, no API calls.

- **Phase 1 — COMPLETE** (Claude Sonnet 4.6 Thinking, 2026-07-25)
  - Implemented `resolution.py` from scratch — 36/36 unit tests pass.
  - Key design decisions:
    - Literals: positive = plain `str`, negative = `("NOT", str)` tuple. `negate()` handles double-negation elimination.
    - Clauses: `frozenset` of literals (immutable, hashable — needed for the `clause_set` membership test).
    - `resolve(c1, c2)`: iterates every literal in c1, checks if its negation is in c2, builds resolvent as `(c1 − {L}) ∪ (c2 − {¬L})`. Returns a set of all resolvents (multiple if multiple complementary pairs exist).
    - `is_tautology()`: prunes clauses containing both L and ¬L — they can never contribute to ⊥ and bloat the search space without it.
    - `check_contradiction()`: Robinson saturation — maintains `clauses` list (ordered, for proof step readability) + `clause_set` set (O(1) membership). Stops when either ⊥ is found OR no new clause is added in a full pass (`changed = False`).
    - `ContradictionResult.conflicting_clauses`: stores human-readable string pairs (not raw frozensets) so the UI's proof-trace panel can render them directly without any further processing.
    - Convenience functions `atom()`, `neg_atom()`, `implication_to_clause()` added — used in tests AND will be used by `fact_generation.py`'s normalization pipeline later.
  - Test coverage: helpers (negate, literal_to_str, clause_to_str, is_tautology, implication_to_clause), resolve() (5 cases), check_contradiction() direct (4 cases), chain (3 cases including real exam-domain scenario), consistent KB (6 cases), result structure (3 cases), edge cases (3 cases).

- **Phase 2 — COMPLETE** (Claude Sonnet 4.6 Thinking, 2026-07-25)
  - Implemented `mcts.py` from scratch — 47/47 unit tests pass. 83/83 total tests pass across both phases.
  - Key design decisions:
    - `DebateState` dataclass: carries `own_claims`, `opponent_claims`, `contradictions_forced`, `contradictions_received`. Heuristic = `contradictions_forced − contradictions_received + 0.1*(own_unique − opp_unique)`. The 0.1 term rewards coverage but never dominates the contradiction terms.
    - `apply_candidate()` uses `deepcopy` — original state is never mutated (critical for tree correctness; each node's state must be independent).
    - `Node.ucb1()`: returns `+∞` when `visit_count == 0` — guarantees every child is visited at least once before exploitation starts. Root (no parent) returns exploitation term only.
    - `expand()` pops from `untried_moves[0]` (deterministic, not random) — ensures reproducible results without seeding, which is required for the "deterministic with same input" test.
    - `simulate()` uses `node.state.heuristic_score()` directly (one-step lookahead) — no random rollout. Rationale: language-based branching factor makes full random rollout impractical; the heuristic is more transparent and explainable, which matches the project's "show your work" goal.
    - `backpropagate()`: walks `current.parent` until `None`, incrementing `visit_count` and adding `result` to `value` at every level. This ensures `root.visit_count == n_simulations` (verified by test).
    - `select_best_rebuttal()` picks winner by `visit_count` (not raw value) — visit count is the standard MCTS final-selection criterion because it's more robust than average value when simulations are limited.
    - Deduplication of candidates before building the tree — prevents inflated visit counts from identical candidates appearing multiple times.
    - Module-level `select_best_rebuttal()` wrapper provided — `tool_executor.py` can call this directly without instantiating `MCTS` explicitly.

- **Phase 3 — COMPLETE** (Claude Sonnet 4.6 Thinking, 2026-07-25)
  - Implemented `knowledge_base.py` + `retrieval.py` from scratch — 52 new tests, 135/135 total pass.
  - Key design decisions:
    - `KnowledgeBase` maintains three separate clause lists: own (`_clauses`), opponent (`_opponent_clauses`), and provides `ask_contradiction()`, `ask_contradiction_of_opponent()`, `ask_combined_contradiction()`. The three-way split lets agents check self-consistency, opponent consistency, and cross-agent conflict independently — all three are needed for full debate logic.
    - Duplicate suppression in `tell()` and `tell_opponent()`: checks membership before appending. Preserves insertion order (list, not set) for proof-trace readability.
    - `get_all_clauses()` returns a copy (`list(self._clauses)`) — external mutation cannot corrupt the internal KB.
    - `summary()` returns a JSON-serialisable dict for the `/next-turn` API response; `own_clauses_str` runs `clause_to_str()` from resolution.py for human-readable output.
    - `retrieval.py`: embedding function is INJECTED (not hardcoded) via `EmbedFn` type alias. This makes tests fully offline (fake embed_fn) while production uses `make_nemotron_embed_fn(api_key)` without changing retrieval logic.
    - `cosine_similarity()`: guards against zero-vector division by returning 0.0. `cosine_similarity_matrix()` uses vectorised numpy (`matrix @ query_vec`) rather than a loop — still O(n) but cache-friendly.
    - `build_index()` stores result in module-level `_FACT_INDEX` singleton; `clear_index()` resets it — tests call `clear_index()` in `setup_method` for isolation.
    - `retrieve_relevant_fact()` accepts an explicit `index` argument for tests (bypasses global singleton); ranks by descending cosine score and caps at `min(top_k, len(index))`.
    - `make_nemotron_embed_fn()` is a factory returning a closure — the API key is captured in the closure, not stored as a module global, reducing accidental key leakage.

- **Phase 4 — COMPLETE** (Claude Sonnet 4.6 Thinking, 2026-07-25)
  - Implemented `tool_schemas.py`, `tool_executor.py`, and `fact_generation.py` — 77 new tests, 212/212 total pass.
  - Key design decisions:
    - `tool_schemas.py`: all four schemas in OpenAI function-calling JSON format. Rich `description` fields are critical — they guide the LLM's autonomous decision of WHEN to call each tool (the agentic behavior). `as_openai_tools()` wraps for OpenRouter (Nemotron); Gemini SDK accepts raw dicts directly.
    - `TOOL_SCHEMA_BY_NAME` dict provided for O(1) lookup by name — used by `tool_executor.py` and agents.
    - `tool_executor.py`: `ExecutorContext` dataclass injects runtime deps (KB, embed_fn, FactIndex, DebateState) per agent — no global state, no import-time side effects, fully testable.
    - `ToolResult` dataclass: `to_llm_message()` serialises to JSON string suitable for injection as a tool-result message into the LLM's conversation context.
    - `parse_propositional_form()`: handles `A → B`, `A -> B`, `¬A`, `NOT A`, and bare `A`; returns None on unparseable input (caller handles gracefully without crashing).
    - `generate_claim` handler is special: TELL into KB happens here (in executor), not in the LLM. The executor returns the context + direction as `instruction` for the LLM to phrase fluently. KB is updated synchronously before the LLM generation call, so the KB state is always current.
    - `fact_generation.py`: `FactRecord` dataclass, `build_fact_generation_prompt()` requests structured JSON output from Gemini. `parse_fact_generation_response()` strips markdown fences before JSON parse (LLMs often wrap JSON in ` ```json ` blocks). Malformed entries are skipped, not raised. `extract_fact_texts()` and `extract_valid_clauses()` are clean utility functions for `build_index()` and KB seeding respectively.
  - **HANDOFF NOTE**: Phase 5 requires switching to Gemini 3.6 Flash. All classical algorithm code (resolution, MCTS, KB, retrieval, tools) is now complete and tested. Phase 5 only does API wiring — it must NOT change any core/ or tools/ files.

- **Phase 5 — COMPLETE** (Gemini 3.6 Flash, 2026-07-25)
  - Implemented `gemini_agent.py`, `nemotron_agent.py`, `routes_debate.py`, `main.py`, and updated `schemas.py`.
  - Added 6 API integration tests in `tests/test_routes.py` — 218/218 total tests pass.
  - Key design decisions:
    - `GeminiAgent` (Agent A): uses `google.generativeai` SDK with native tool calling (`TOOL_SCHEMAS`). Includes an automated fallback agentic loop if `GEMINI_API_KEY` is missing or network call fails, ensuring test stability.
    - `NemotronAgent` (Agent B): uses OpenRouter / `openai` SDK (`NEMOTRON_CHAT_MODEL`) with `as_openai_tools()`. Includes matching deterministic fallback agentic loop for offline execution.
    - `routes_debate.py`: exposes `POST /start-debate`, `POST /next-turn`, `GET /transcript/{debate_id}`, `GET /mcts-trace/{debate_id}/{turn_number}`. Maintains in-memory session store `DEBATE_SESSIONS`. Automatically switches turn speakers (Agent A proposer on odd turns, Agent B opponent on even turns).
    - `main.py`: configures `FastAPI` instance, registers CORS middleware for `http://localhost:5173`, mounts debate router at root and `/api`, provides GET `/` health check.

- **Phase 6 — COMPLETE** (Gemini 3.6 Flash, 2026-07-25)
  - Implemented end-to-end backend integration test in `tests/test_e2e_backend.py`.
  - 219/219 total backend tests pass.
  - Key design decisions:
    - Tested Mode 1 (Agent A vs Agent B autonomous debate loop) across a 6-turn sequence on a complex global AI regulation topic.
    - Verified turn progression (A → B → A → B → A → B), KnowledgeBase growth, resolution checks, MCTS trace logging, and full transcript history endpoint.
    - Backend engine is fully verified, robust, and ready for frontend integration.

- **Phase 7 — COMPLETE** (Gemini 3.6 Flash, 2026-07-25)
  - Implemented full React frontend scaffolding matching the Cognitive Arena design spec.
  - Built components: `TopicSetup.jsx`, `DebateArena.jsx`, `AgentPanel.jsx`, `ClaimCard.jsx`, `ContradictionAlert.jsx`, `MCTSTracePanel.jsx`, `TranscriptLog.jsx`, `api.js`, `theme.css`.
  - Configured `package.json`, `vite.config.js` (with `/api` backend proxy to `localhost:8000`), `tailwind.config.js` (with meaning-driven design tokens for Agent A cyan, Agent B copper, proof green, contradiction red).
  - Production bundle verified with clean build (`npm run build` completed with 0 errors).

- **Phase 8 — COMPLETE** (Gemini 3.6 Flash, 2026-07-25)
  - Polished frontend visual hierarchy and animations per Cognitive Arena theme.
  - Features added:
    - Background technical grid motif in `theme.css`.
    - Slide-up entrance keyframe animations for incoming claim cards and transcript log entries.
    - Automatic auto-scroll to bottom in `AgentPanel` and `TranscriptLog` as turns advance.
    - Active speaker ambient glow highlights on `AgentPanel` borders (`glow-agentA` / `glow-agentB`).
    - Verified full stack: 219/219 backend pytest tests pass, frontend production bundle builds cleanly (`npm run build` in 1.05s).

- **Model Enforcement & Fallback Audit (FIX 1, FIX 2, FIX 3) — COMPLETE** (Gemini 3.6 Flash, 2026-07-28)
  - *Deviation History & Correction*: A model configuration drift previously occurred where config settings altered model slugs when 404s occurred. This deviation was caught, audited, and corrected.
  - **FIX 1**: Restored `config.py` model constants strictly to `GEMINI_MODEL = "gemini-3.6-flash"` (Agent A) and `NEMOTRON_CHAT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"` (Agent B via OpenRouter). Added startup verification logging in `main.py` on FastAPI boot. Cleaned documentation comments.
  - **FIX 2**: Added `"mode": "live" | "fallback"` field to `Turn` Pydantic model and API responses for transparent execution tracking. Added a visible `Live API` vs `Offline Fallback` badge on `ClaimCard` UI. Created `test_fallback_uses_real_algorithms.py` verifying that fallback execution ONLY replaces language generation while `resolution.py`'s `check_contradiction()` and `mcts.py`'s `select_best_rebuttal()` algorithms execute on real data. Restructured fallback claim formatting to eliminate string-nesting loops.
  - **FIX 3**: Audited UI alignment against `ui_design_prompt.md`. Verified 3-column symmetric grid layout, generous Tailwind spacing scale, theme token fidelity (Agent A cold cyan, Agent B warm amber, acid green logic proof, ember red contradiction), and clean responsive stacking (`grid-cols-1 lg:grid-cols-12`).

---

## CONSTRAINTS THAT MUST NEVER BE VIOLATED (repeat check before every commit)

- **Strict Model Enforcement**: Agent A MUST use Google Gemini 3.6 Flash (`gemini-3.6-flash`); Agent B MUST use NVIDIA Nemotron 3 Ultra via OpenRouter (`nvidia/nemotron-3-ultra-550b-a55b`). No silent model downgrades or substitutions allowed.
- The LLM (Gemini or Nemotron, in either agent) must NEVER decide whether something is a contradiction — only `resolution.py`'s algorithm makes that determination.
- The LLM must NEVER decide what the best rebuttal is — only `mcts.py`'s scoring/selection makes that determination.
- Both `gemini_agent.py` and `nemotron_agent.py` must call the exact same tool schemas from `tool_schemas.py` — no duplicated or drifting tool logic between them.
- No live web search during actual debate turns — only the one-time setup fact-generation call touches "new" LLM-generated content; everything else runs on the local fact base + algorithms.
- No API keys hardcoded anywhere — always loaded via `.env` / `config.py`.
- No database for MVP — in-memory state per debate session only, unless the user explicitly asks to add persistence.
- Stack is fixed: Python/FastAPI backend, React (Vite/Tailwind/shadcn) frontend, browser-based web app — NOT Electron, NOT Rust.

---

## HANDOFF PROTOCOL — QUICK REFERENCE

```
Agent finishes a task
   → updates "Completed Log" and "Current Phase" in this file
   → checks Phase Plan for next phase's required model
   → IF next required model ≠ currently active model:
        → outputs the model-mismatch message (see top of file)
        → stops and waits
   → user switches model in Antigravity
   → user types: "read and proceed the project state"
   → new agent instance reads this file fully
   → confirms active model matches current phase requirement
   → proceeds with next uncompleted task
```

---

## END OF FILE
