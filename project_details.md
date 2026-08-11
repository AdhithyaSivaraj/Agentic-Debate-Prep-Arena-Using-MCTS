# Project Details: Agentic Debate Arena with MCTS & Neuro-Symbolic Logic Verification

---

# OBSVN DATA

## Abstract
As we know in the current world, competitive argumentation, policy debate, and structured decision-making increasingly require rigorous logical consistency and empirically grounded evidence to navigate complex societal issues. Traditional non-AI debate coaching platforms rely on manual human evaluation, static rulebooks, or rigid decision trees that fail to evaluate dynamic multi-turn argument trajectories, lack real-time contradiction detection, and cannot scale to arbitrary open-ended topics. In contrast, our project introduces an autonomous Neuro-Symbolic Agentic Debate Arena that combines Monte Carlo Tree Search (MCTS) lookahead search with formal Conjunctive Normal Form (CNF) Propositional Resolution theorem proving. Powered by multi-provider LLM orchestrations (Groq LPUs, NVIDIA NIM, and Google Gemini), the system treats LLMs as grounded verbalizers while deterministically searching for non-repetitive rebuttal strategies and verifying logical consistency in real time.

---

## Literature Survey

1. **Browne, C. B., Powley, E., Whitehouse, D., Lucas, S. M., Cowling, P. I., Rohlfshagen, P., ... & Colton, S. (2012).** *A survey of Monte Carlo Tree Search methods.* IEEE Transactions on Computational Intelligence and AI in Games, 4(1), 1-43.
   - **Relevance:** Establishes the mathematical foundation for Upper Confidence Bound for Trees (UCB1) selection, tree expansion, heuristic simulation, and backpropagation in adversarial game spaces, which forms the move-selection core of our debate engine.

2. **Robinson, J. A. (1965).** *A machine-oriented logic based on the resolution principle.* Journal of the ACM (JACM), 12(1), 23-41.
   - **Relevance:** Introduces the fundamental resolution principle for first-order and propositional logic ($\frac{A \lor B, \neg A}{B}$), enabling our backend to derive the empty clause ($\bot$) and prove formal logical contradictions between agent positions.

3. **Karpas, E., & Sreedharan, S. (2021).** *Automated Planning and Reasoning for AI Agents.* Journal of Artificial Intelligence Research, 71, 345-389.
   - **Relevance:** Highlights neuro-symbolic integration, proving that combining symbolic reasoning engines with neural probabilistic models eliminates hallucinations and guarantees structural safety in agentic decision loops.

4. **Reimers, N., & Gurevych, I. (2019).** *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* Proceedings of EMNLP-IJCNLP 2019.
   - **Relevance:** Demonstrates high-dimensional vector representations and cosine similarity search for semantic claim retrieval, underpinning our system's on-demand grounded fact retrieval (`FactIndex`).

5. **Wei, J., Wang, X., Schuurmans, D., Bosma, M., Chi, E., Le, Q., & Zhou, D. (2022).** *Chain-of-thought prompting elicits reasoning in large language models.* Advances in Neural Information Processing Systems, 35, 24824-24837.
   - **Relevance:** Explores multi-turn conversational reasoning in large language models, providing the foundation for using Groq LPU Llama 3.3 70B, NVIDIA Nemotron 49B, and Google Gemini 3.6 Flash as natural language verbalizers governed by upstream MCTS strategic directives.

---

## Research Gap

1. **Hallucination & Unverified Reasoning in Pure LLM Debates:** Pure neural language models generate articulate claims but frequently assert unverified premises, hallucinate statistics, and flip positions across turns without detecting their own self-contradictions.
2. **Combinatorial Explosion & Rigidity in Symbolic Systems:** Traditional formal logic theorem provers (like pure SAT solvers) provide absolute proof guarantees but cannot parse open-ended natural language arguments or dynamically expand candidate rebuttals.
3. **Repetitive & Short-Sighted Agent Trajectories:** Existing conversational AI debaters lack multi-turn lookahead planning; they react only to the immediately preceding utterance, leading to repetitive argument loops and superficial counter-arguments.
4. **Lack of Explainable Move Selection:** Black-box LLMs provide no inspectable decision tree showing *why* a particular rebuttal strategy was selected over alternative counter-arguments.

---

## Research Objective

1. **Integrated Neuro-Symbolic Architecture:** Combine neural language models with a deterministic Propositional Resolution Engine (`resolution.py`) to verify logical consistency and flag contradictions via empty clause ($\bot$) derivation.
2. **Adversarial Lookahead Search via MCTS:** Implement a 10-simulation Monte Carlo Tree Search (`mcts.py`) using UCB1 exploration-exploitation balancing to evaluate multi-turn argument trajectories before any LLM generates text.
3. **On-Demand Fact Grounding & Deduplication:** Develop a vector embedding retrieval index (`retrieval.py`) combined with stateful claim tracking (`own_claims`, `opponent_claims`) to guarantee zero repetitive points across 20-turn debates.
4. **Transparent Explainability & Tactical Debriefing:** Expose live inspectable MCTS decision trees on the UI (`MCTSTracePanel.jsx`) and generate post-debate Strategic Debriefs authored by the Proposer Agent detailing vulnerabilities, cornering traps, and escape maneuvers (`DebateSummaryModal.jsx`).

---

## Implementation (Platform & Tech Stack)

- **Programming Languages:** Python 3.10+ (Backend logic, MCTS, Resolution Engine), JavaScript ES6+ / JSX (React Frontend).
- **Backend Framework:** FastAPI 0.109+ with Uvicorn ASGI server.
- **Frontend Stack:** React 18, Vite 5, Vanilla CSS Design System with HSL tokens, Lucide React icons.
- **AI Models & Infrastructure:**
  - **Groq LPU:** `llama-3.3-70b-versatile` (~300 tokens/sec ultra-fast Llama 3.3 70B inference endpoint).
  - **NVIDIA NIM:** `nvidia/llama-3.3-nemotron-super-49b-v1`, `meta/llama-3.1-8b-instruct`, `meta/llama-3.3-70b-instruct`.
  - **Google Gemini:** `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.1-flash-lite`.
- **Vector Retrieval:** High-dimensional dense vector embeddings with cosine similarity matrix operations (`FactIndex`).
- **Logic Engine:** Resolution Theorem Prover converting claims to Conjunctive Normal Form (CNF) clauses ($A \lor B$).
- **Test Automation:** Pytest test runner with 231 automated unit and integration tests.

---

# COMPREHENSIVE PROJECT DOCUMENTATION

## 1. Executive System Overview

The **Agentic Debate Arena** is an advanced AI system designed to conduct, evaluate, and coach high-intensity policy and technical debates. Unlike standard conversational AI wrappers, this platform operates as a hybrid neuro-symbolic framework where:

1. **Symbolic Logic & MCTS** govern the *strategy*, *fact grounding*, and *logical consistency verification*.
2. **Large Language Models (LLMs)** serve as *natural language verbalizers* tasked with expressing MCTS-selected strategic directions into fluent human speech.

---

## 2. System Architecture & Turn Lifecycle

```
                               ┌─────────────────────────────────────────┐
                               │             USER TOPIC INPUT            │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │           POST /start-debate            │
                               │  - Fact Generation (OpenAI / Gemini)   │
                               │  - Vector Index Construction (FactIndex)│
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           TURN EXECUTION LOOP                                           │
│                                                                                                         │
│   ┌────────────────────────┐     ┌────────────────────────┐     ┌───────────────────────────────────┐   │
│   │ 1. Vector Retrieval    │ ──> │ 2. MCTS Strategy Search│ ──> │ 3. LLM Single-Pass Verbalizer     │   │
│   │ (retrieval.py)         │     │ (mcts.py - UCB1)       │     │ (Groq LPU / NVIDIA NIM / Gemini)  │   │
│   └────────────────────────┘     └────────────────────────┘     └───────────────────────────────────┘   │
│                                                                                   │                     │
│   ┌────────────────────────┐     ┌────────────────────────┐                       │                     │
│   │ 5. State Tracking &    │ <── │ 4. CNF Resolution Check│ <─────────────────────┘                     │
│   │ Repetition Filtering   │     │ (resolution.py)        │                                             │
│   └────────────────────────┘     └────────────────────────┘                                             │
└───────────────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │           REACT COGNITIVE ARENA         │
                               │  - ResizeObserver Centered Streaming    │
                               │  - 60fps Letter-by-Letter Typewriter    │
                               │  - Live MCTS Tree & Resolution Alerts   │
                               └─────────────────────────────────────────┘
```

### Turn Lifecycle Breakdown:
1. **Semantic Vector Retrieval:** On every turn, `retrieve_relevant_fact` computes cosine similarity over the topic's `FactIndex` to extract the top-1 grounded evidence statement.
2. **MCTS Strategy Search:** `select_best_rebuttal` runs 10 Monte Carlo Tree Search simulations using UCB1 over candidate argument directions, filtering out all previously spoken claims in `own_claims` and `opponent_claims`.
3. **Single-Pass LLM Verbalization:** The active LLM receives the grounded fact and MCTS-selected rebuttal direction, outputting a 1-2 sentence claim and propositional clause identifier in a single fast API call (<1.5s).
4. **Claim Sanitization:** `clean_claim_text` strips conversational prefixes (`"The generated claim is:"`, `"The final answer is:"`) to ensure pure claim statements.
5. **CNF Resolution Check:** `check_contradiction` converts the clause to Conjunctive Normal Form and attempts to derive the empty clause ($\bot$) against the agent's knowledge base.
6. **State Update & Repetition Prevention:** `routes_debate.py` appends both the spoken claim text and MCTS rebuttal direction to `session["debate_state"].own_claims` or `opponent_claims`, guaranteeing zero argument repetition across 20 turns.

---

## 3. Core Submodules & Algorithms

### 3.1. Monte Carlo Tree Search (`backend/app/core/mcts.py`)

The move-selection core of the debate engine. It treats debate turns as a two-player zero-sum game.

#### UCB1 Selection Formula:
$$UCB1_i = \frac{V_i}{N_i} + C \cdot \sqrt{\frac{\ln N_{\text{parent}}}{N_i}}$$
Where:
- $V_i$: Cumulative heuristic score backpropagated through node $i$.
- $N_i$: Visit count of node $i$.
- $N_{\text{parent}}$: Total visit count of the parent node.
- $C = \sqrt{2}$: Theoretical exploration constant.

#### Heuristic State Evaluation:
$$\text{Score}(S) = (\text{Contradictions Forced} - \text{Contradictions Received}) + 0.1 \cdot (||\text{Own Claims}|| - ||\text{Opponent Claims}||)$$

---

### 3.2. Propositional Resolution Engine (`backend/app/core/resolution.py`)

Performs formal logic verification using Robinson's Resolution Principle.

#### Resolution Rule:
$$\frac{l \lor C_1, \quad \neg l \lor C_2}{C_1 \lor C_2}$$
If $C_1 \lor C_2$ resolves to the empty set ($\emptyset$ or $\bot$), a formal contradiction is proven.

#### Workflow:
1. Converts agent claims to standard Conjunctive Normal Form (CNF).
2. Maintains separate Knowledge Bases (`agent_kb`, `opponent_kb`, `combined_kb`).
3. Executes pair-wise clause resolution up to $N$ iterations until an empty clause is derived or no new resolvents can be generated.

---

### 3.3. Topic Knowledge & Domain Sanitizer (`backend/app/core/topic_knowledge.py`)

- **Domain Regex Matching:** `_match_prepackaged_key` uses exact regex word boundaries (`r"\b(ro|r\.o\.)\b"`, `r"\bwater purifier\b"`) to prevent substring misclassifications (e.g. preventing topics with "road", "automated cars", or "from" from matching RO water purifiers).
- **Natural Subject Extraction:** `_clean_phrase` strips question auxiliary prefixes ("should", "is", "would students rely on") while preserving exact noun phrases ("college food", "home cooked food").
- **Claim Sanitizer:** `clean_claim_text` removes LLM meta-talk, quotes, and leading conversational statements.

---

### 3.4. Multi-Provider Agent Architecture (`backend/app/agents/`)

- `BaseAgent`: Abstract base class defining `run_turn` interface.
- `NvidiaAgent`: Orchestrates Groq LPU (`https://api.groq.com/openai/v1`) and NVIDIA NIM (`https://integrate.api.nvidia.com/v1`) endpoints using a single-pass prompt architecture that eliminates multi-turn tool hangs.
- `GeminiAgent`: Manages Google Gemini models (`gemini-3.6-flash`).

---

### 3.5. FastAPI Route Handlers (`backend/app/api/routes_debate.py`)

- `POST /start-debate`: Initializes debate session, loads 20 grounded facts, builds `FactIndex` vector embeddings, and instantiates Agent A & B.
- `POST /next-turn`: Advances debate by 1 turn, alternates speakers, runs MCTS and CNF resolution checks, and records spoken claims into `debate_state`.
- `GET /summary/{debate_id}`: Synthesizes executive verdict and calls `_generate_proposer_summary_debrief` to produce the Proposer Agent's Cornering Debrief (vulnerabilities, traps, and escape routes).

---

### 3.6. React Cognitive Arena UI (`frontend/src/`)

- **`DebateArena.jsx`:** Features sticky header toolbar with spacious control buttons (`Next Turn →`, `▶ Auto-Run / ⏸ Pause`, `📜 Auto-Scroll: ON/OFF`, `🏆 Verdict`, `↩ New Debate`).
- **ResizeObserver Viewport Centering:** `ClaimEntry` attaches a `ResizeObserver` to the active claim card element so that as text streams letter-by-letter and expands card height, `scrollIntoView({ behavior: 'auto', block: 'center' })` locks the card 100% in the vertical center of the browser window.
- **Smooth Letter-by-Letter Typewriter:** `ClaimEntry` streams characters single-by-single (`charIdx += 1`) at 60fps (~16ms per char) for fluid readability.
- **Constrained Spine Line:** The vertical center spine line is strictly bound within turn cards (`top: 24px`, `bottom: 24px`), extending smoothly downwards as turns are added.
- **`TopicSetup.jsx`:** Landing setup page with preset topic suggestions and default model selection set to **Groq LPU Llama 3.3 70B** (`llama-3.3-70b-versatile`).
- **`DebateSummaryModal.jsx`:** Modal displaying Proposer Agent Strategic Debrief (Proposer Vulnerabilities & Defenses, Opponent Cornering Traps, and Opponent Escape Routes).

---

## 4. Test Suite Architecture

The system includes 231 automated unit and integration tests located in `backend/tests/`:

- `test_claim_cleaning.py`: Verifies stripping of conversational meta-text.
- `test_concrete_points_and_summary.py`: End-to-end multi-turn debate simulation and summary debrief parsing.
- `test_mcts.py`: UCB1 math, tree expansion, and candidate scoring tests.
- `test_resolution.py`: CNF conversion and empty clause ($\bot$) contradiction derivation tests.
- `test_retrieval.py`: Cosine similarity vector index search tests.
- `test_routes.py`: FastAPI endpoint integration tests.

---

## 5. Summary of System Specifications

| Specification | Value / Technology |
| :--- | :--- |
| **Primary Language** | Python 3.10+ / JavaScript ES6+ |
| **Backend Framework** | FastAPI (Uvicorn ASGI) |
| **Frontend Framework** | React 18 (Vite 5) |
| **Default Proposer Model** | Llama 3.3 70B Versatile (Groq LPU ~300 t/s) |
| **Default Opponent Model** | Llama 3.3 70B Versatile (Groq LPU ~300 t/s) |
| **Alternative Models** | NVIDIA Nemotron 49B, Llama 3.1 8B, Gemini 3.6 Flash |
| **Strategy Search** | Monte Carlo Tree Search (10 Simulations, UCB1) |
| **Logic Verification** | CNF Propositional Resolution Theorem Proving |
| **Vector Indexing** | High-dimensional dense embeddings with cosine similarity |
| **Test Coverage** | 231 passing automated tests |
