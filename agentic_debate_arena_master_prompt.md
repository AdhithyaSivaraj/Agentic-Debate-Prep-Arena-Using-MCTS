# MASTER PROJECT PROMPT — "Agentic Debate Arena: Logic-Verified Argument Coaching"

## CONTEXT: WHO IS ASKING AND WHY

I am a student working on a course project for **"Foundations of AI"**, a college-level course covering four units:
- **Unit I** — Introduction to AI: History, Types/Domains of AI, Intelligent Agents (Agents and Environments), Rationality, Nature of Environments, Structure of Agents, Problem-Solving Agents, Search Algorithms, Uninformed Search
- **Unit II** — Problem Solving: Informed (Heuristic) Search, Local Search and Optimization, Local Search in Continuous Spaces, Search with Nondeterministic Actions, Search in Partially Observable Environments, Online Search Agents
- **Unit III** — Game Playing and CSP: Game Theory, Optimal Decisions in Games, Heuristic Alpha-Beta Tree Search, Monte Carlo Tree Search, Stochastic Games, Partially Observable Games, Defining CSPs, Constraint Propagation, Backtracking Search for CSPs
- **Unit IV** — Logical Reasoning: Knowledge-Based Agents, Propositional Logic, Propositional Theorem Proving, Effective Propositional Model Checking, Agents Based on Propositional Logic, First-Order Logic Representation, Syntax/Semantics of FOL, Knowledge Engineering in FOL, Forward Chaining, Backward Chaining, Resolution

**The assignment**: design and build a project that (a) uses at least one algorithm/technique taught in this syllabus, (b) applies it to a real, underexplored problem, and (c) additionally incorporates "agentic AI" as an extra requirement layered on top of the classical algorithm work.

**My constraint**: I need this to be genuinely mine and hard for classmates to have picked independently — the class defaults to single-technique, single-unit projects (e.g., "N-Queens with backtracking" or "8-puzzle with A*"). I deliberately chose to chain multiple units together and pair classical, explainable algorithms with an LLM-based agentic wrapper, because that combination is uncommon both among student projects and in the broader research/product landscape (verified via web search — multi-agent LLM debate exists as a research area, but virtually all existing systems use the LLM's own implicit judgment to detect contradictions and pick arguments; almost none use hard symbolic algorithms as separate, auditable modules alongside the LLM).

---

## THE PROJECT: "Agentic Debate Arena: Logic-Verified Argument Coaching"

### One-line problem statement
An agentic AI system where two independently-modeled debater agents argue a topic using only locally-verified facts, with propositional resolution catching logical contradictions and Monte Carlo Tree Search selecting each side's optimal rebuttal — replacing an LLM's implicit judgment with explainable, provable classical AI reasoning.

### Why this is novel (be honest about this, don't oversell)
- Multi-agent LLM debate is NOT novel by itself — it's an active, published research area (LLM debate for factuality, self-consistency, LLM-as-judge frameworks all exist).
- What IS the genuine, defensible contribution: replacing the LLM's own black-box judgment (of "who won," "is this a contradiction," "what's the best comeback") with **hard, deterministic, explainable classical AI algorithms** taken directly from the course syllabus — resolution for contradiction detection (provable, not guessed) and MCTS for move selection (simulated lookahead, not free-form generation).
- The LLMs (Gemini + Nemotron) are demoted to being the **language/orchestration layer only** — they phrase things fluently and decide when to call tools — while the actual "AI reasoning" that earns the grade is 100% classical algorithms from the syllabus.
- Do NOT claim this is a "world first" or that "nobody has ever done this" — frame it precisely as: existing debate systems judge with the LLM itself; this project swaps that for auditable symbolic reasoning, which is a specific, correctly-scoped, defensible novelty claim for a course project.

### Three usage modes to support (in order of build priority)
1. **Agent vs Agent** (build this first — the core engine): two AI debaters argue autonomously, no human involved, given only a topic.
2. **User + Agent (co-op) vs Agent**: the agent helps the user refine/strengthen their own arguments against an opposing agent (coaching mode).
3. **User vs Agent** (direct): the user debates the agent directly, and the agent gives explainable feedback on the user's logical consistency.

Mode 1 is the MVP / demo core. Modes 2 and 3 are extensions once Mode 1 works end-to-end.

---

## WHY IT QUALIFIES AS "AGENTIC AI" (not just "using an LLM")

An LLM call is NOT agentic by itself. It becomes agentic only when it satisfies ALL of these:
1. **Autonomy** — the system runs the debate itself, turn after turn, without a human manually prompting each line.
2. **Tool use** — the LLM calls external tools/functions mid-reasoning (resolution checker, MCTS selector, fact retriever) rather than generating everything from its own "memory."
3. **Loop with persistent state** — each agent maintains and updates its own knowledge base (its accumulated claims) across turns, and reacts to what was said earlier — not a single one-shot prompt/response.
4. **Autonomous decision-making about tool use** — the agent itself decides WHEN to call which tool (e.g., "check for contradiction after every claim," "run MCTS before every rebuttal") rather than a human hardcoding the sequence turn-by-turn.

This system satisfies all four: it is a genuine agentic system, not a scripted chatbot wrapper.

---

## SYLLABUS COVERAGE

### Topics covered (by unit)
- **Unit I**: Intelligent Agents — Agents and Environments; Knowledge-Based Agents (as an architectural framing for how each debater is structured: percepts = opponent's last claim, actions = next claim/rebuttal, performance measure = contradictions forced minus contradictions received)
- **Unit II**: Search Strategies — applied as informed/semantic search over a local knowledge base (via embedding similarity), used for fact retrieval before each claim
- **Unit III**: Game Theory; Adversarial Search — the debate itself is framed as an adversarial two-player game
- **Unit IV**: Propositional Logic; Knowledge-Based Agents (TELL/ASK architecture); Propositional Theorem Proving

### Algorithms actually implemented (the graded core — must be real, working code, not just LLM prompting)
1. **Resolution (Propositional Theorem Proving)** — Unit IV. After every turn, convert the agent's claim into propositional clause form (e.g., `Exams → StressHigh`, `¬StressHigh ∨ ¬HealthGood`), add to that agent's running knowledge base, and run the resolution algorithm to check whether any pair of clauses resolves to the empty clause (⊥ = contradiction). This must be an actual resolution-refutation implementation (clause resolution, unification/negation handling for propositional literals), not an LLM asked "is this a contradiction?"
2. **Monte Carlo Tree Search (MCTS)** — Unit III. At each turn, generate N candidate rebuttals, build a shallow game tree of likely follow-up exchanges (your move → opponent's likely counter → your likely counter-counter), and run the four standard MCTS phases (Selection, Expansion, Simulation, Backpropagation) scoring leaf nodes by a heuristic (e.g., number of opponent claims contradicted minus number of own claims left vulnerable). Pick the rebuttal with the best backpropagated score. Must be real MCTS, not just "ask the LLM to think of a comeback."
3. **Best-First / Semantic Search** — Unit II (and I). Implemented via embedding similarity search (using NVIDIA Nemotron 3 Embed 1B) over a locally-held fact base, to retrieve the most relevant fact for grounding a claim. This satisfies the syllabus's "search" requirement using a real similarity/priority-based retrieval mechanism, not naive keyword matching.

### Architectural concept from syllabus (not a standalone algorithm, but must be explicitly named/documented)
- **Knowledge-Based Agent (TELL/ASK pattern)**, Unit IV — each debater is formally structured as a KB agent: `TELL(kb, new_claim)` adds a claim to its knowledge base; `ASK(kb, contradiction_query)` queries the KB via the resolution algorithm.

---

## SYSTEM ARCHITECTURE

```
User picks a topic (e.g., "Should exams be abolished?")
        ↓
[ONE-TIME SETUP] Gemini generates 20–25 factual claims about the topic,
   each with explicit logical relationships (supports/contradicts/implies)
        ↓
[NORMALIZATION STEP] Parse/clean LLM output into strict propositional
   clause form (A → B, A ∧ B → C, etc.) — this local fact base doubles as
   (a) the graph for semantic search retrieval AND (b) seed clauses for
   the resolution knowledge base
        ↓
        ┌─────────────────────────┐        ┌─────────────────────────┐
        │   Agent A (Proposer)    │  <-->  │   Agent B (Opponent)    │
        │   Brain: Gemini API     │        │   Brain: Nemotron 3     │
        │   (function calling)    │        │   Ultra (OpenRouter,    │
        │                         │        │   free, tool-calling    │
        │                         │        │   capable)              │
        │                         │        │                         │
        │  Loop per turn:         │        │  Loop per turn:         │
        │  1. retrieve_fact()     │        │  1. retrieve_fact()     │
        │  2. generate_claim()    │        │  2. generate_claim()    │
        │  3. TELL(kb, claim)     │        │  3. TELL(kb, claim)     │
        │  4. check_contradiction │        │  4. check_contradiction │
        │     (resolution algo)  │        │     (resolution algo)  │
        │  5. select_rebuttal()   │        │  5. select_rebuttal()   │
        │     (MCTS algo)        │        │     (MCTS algo)        │
        └─────────────────────────┘        └─────────────────────────┘
                        ↓
        Debate transcript + contradiction log (with proof trace)
        + winner/score based on contradictions forced vs. received
```

**Why two different LLMs (Gemini for Agent A, Nemotron 3 Ultra for Agent B) instead of one model role-playing both sides**: a single model arguing with itself tends to be less genuinely adversarial/oppositional (it "knows" both sides are itself). Two distinct models produce more authentic, independent reasoning styles, which strengthens the adversarial framing from Unit III's game theory. This is a deliberate design choice — document it as such.

---

## TOOLS (functions) THE AGENTS CALL

| Tool name | Purpose | Underlying mechanism | Called by |
|---|---|---|---|
| `retrieve_relevant_fact(claim_topic)` | Find the most relevant fact from the local fact base for grounding a claim | Embedding similarity search using Nemotron 3 Embed 1B + cosine similarity (Unit II search) | Both agents, before making any claim |
| `check_contradiction(agent_kb)` | Detect logical contradictions in an agent's accumulated claims | Propositional resolution algorithm (Unit IV) — returns whether the empty clause is derivable, plus which clauses conflict | Both agents, after every turn (their own KB) and optionally to check the opponent's KB |
| `select_best_rebuttal(candidate_list)` | Choose the strongest next argument from several candidates | Monte Carlo Tree Search over a shallow game tree of simulated future exchanges (Unit III) | The agent responding to an attack/contradiction |
| `generate_claim(context, kb_state)` | Produce a fluent, natural-language argument or rebuttal | LLM call (Gemini function calling, or Nemotron 3 Ultra native tool-use) | Both agents, every turn — this is the ONLY step where the LLM freely generates language; all reasoning/selection logic lives in the other three tools |

**Both Gemini and Nemotron 3 Ultra must be wired to the SAME tool schema/functions** (define tools once in an OpenAI-function-calling-compatible JSON schema; both APIs support this format via OpenRouter/native Gemini function calling) — this avoids duplicated logic and proves both "brains" can operate the identical reasoning engine.

**Nemotron 3 Ultra tool-calling note**: confirmed to have strong, purpose-built tool-use behavior for exactly this kind of agentic loop (plan → call tool → read result → repeat), via OpenRouter, with a free tier (verify current request/day quota before final demo — was ~200 req/day free tier as of research, subject to change).

**Nemotron 3 Embed 1B note**: this is an embeddings-only model — it does NOT generate chat/text, it only turns text into vectors. Pair it with your own cosine-similarity function in code; do not attempt to call it as a chat/reasoning model.

---

## FREE MODEL/API STACK (cost-conscious, demo-safe)

- **Gemini API (Google AI Studio)** — free tier, generous daily quota (~1,500 req/day on Flash-tier models as of research), supports native function/tool calling, large context window. Used as Agent A's brain and/or the setup-phase fact generator.
- **Nemotron 3 Ultra (free)** via **OpenRouter** — frontier open reasoning/orchestration model (55B active / 550B total MoE params), 1M token context, purpose-built for long agentic tool-calling loops. Used as Agent B's brain.
- **Nemotron 3 Embed 1B (free)** via **OpenRouter** — embedding-only model for the fact-retrieval "search" component.
- All three are free-tier / no-credit-card-required options, chosen specifically because of student/zero-budget constraints.
- Build in a fallback/retry pattern (e.g., if one API errors mid-demo, gracefully degrade or retry) since free tiers can rate-limit or have outages — do NOT depend on live internet fact retrieval during the actual debate turns; only the one-time setup call touches "generation," everything else runs on locally-held data + your own algorithm code.

---

## WHAT MUST BE ACTUAL HAND-WRITTEN CODE (this is where the grade lives) vs. WHAT THE LLM DOES

**Must be real, from-scratch (or from-first-principles, no black-box library shortcuts) implementations:**
- Propositional clause resolution algorithm (resolution refutation)
- MCTS (selection/expansion/simulation/backpropagation phases, with a real tree structure and a defined heuristic/scoring function)
- Cosine similarity search over embeddings for fact retrieval
- The KB agent's TELL/ASK interface

**What the LLMs (Gemini/Nemotron) are allowed to do:**
- One-time: generate the initial fact base from a topic (then it gets normalized/parsed into strict logical form by your code)
- Every turn: phrase the chosen move (selected by MCTS) into natural, fluent argumentative language
- Every turn: convert a natural-language claim into propositional literal form for the resolution engine (a parsing/formalization task, not the reasoning itself)
- Decide (via function-calling reasoning) which tool to invoke next in the loop

**The dividing line to keep sacred**: the LLM never DECIDES whether something is a contradiction, and never DECIDES what the best rebuttal is — those are the outputs of your resolution and MCTS code respectively. The LLM only phrases and formalizes language; your syllabus algorithms make the actual reasoning decisions. This is the entire point of the project and must be preserved in the final implementation — do not let convenience push logic-checking or move-selection into a raw LLM prompt.

---

## DELIVERABLES / BUILD ORDER (recommended)

1. Local fact base structure + normalization pipeline (topic → LLM-generated facts → parsed propositional clauses)
2. Resolution engine (unit tested on hand-crafted contradiction examples first, before connecting to LLM-generated data)
3. Embedding-based fact retrieval (Nemotron 3 Embed 1B + cosine similarity)
4. MCTS move-selector (test on a toy game tree first, then connect to real candidate rebuttals)
5. Agent loop wiring: Gemini function calling for Agent A, Nemotron 3 Ultra function calling for Agent B, both pointed at the same four tools
6. Full end-to-end Agent-vs-Agent debate demo (Mode 1)
7. Transcript/UI output showing: the debate turn-by-turn, contradiction proof traces when found, and the MCTS-selected move highlighted vs. rejected alternatives (this "show your work" visualization is a major demo strength — it's what makes the "explainable, not black-box" pitch concrete and visible)
8. (Stretch) Modes 2 and 3 — user-in-the-loop coaching and direct user-vs-agent debate

---

## REPORT / PITCH FRAMING (use this language, it's calibrated and defensible)

> "Multi-agent LLM debate is an active research area, but existing systems rely on the LLM's own implicit judgment to detect contradictions and choose arguments. This project replaces that black-box judgment with two classical, explainable AI techniques from the course syllabus — propositional resolution for provable contradiction detection, and Monte Carlo Tree Search for principled move selection — making the reasoning auditable rather than purely LLM-generated. The LLMs (Gemini and Nemotron 3 Ultra) are used only for natural-language generation and as the autonomous orchestration layer that decides when to invoke each classical algorithm, satisfying the agentic AI requirement while keeping the graded algorithmic core — resolution, MCTS, and semantic search — fully explainable and directly traceable to Units II, III, and IV of the syllabus."

---

## TITLE

**"Agentic Debate Arena: Logic-Verified Argument Coaching"**

---

## END OF CONTEXT DUMP

Everything above is the complete state of this project as discussed and decided. Nothing here should be silently changed (e.g., swapping resolution/MCTS for pure LLM judgment, or dropping the two-different-LLM-brains design) without flagging it as a deviation from the original plan, since the specific choices above are what make the novelty/defensibility argument work.
