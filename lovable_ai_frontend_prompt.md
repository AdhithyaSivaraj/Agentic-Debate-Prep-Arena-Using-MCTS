# Agentic Debate Arena — Lovable AI Frontend Master Specification & Prompt

> **Purpose:** This file contains all technical specifications, data schemas, API contracts, design rules, and complete code primitives required to build the entire frontend for **Agentic Debate Arena** in Lovable AI.

---

## 1. Executive Brief & Core Concept

**Agentic Debate Arena** is an explainable AI argument coaching engine where two autonomous AI agents debate a user-defined topic:
- **Agent A (Proposer):** Gemini 3.6 Flash
- **Agent B (Opponent):** Nemotron 3 Ultra / Gemini

### What makes it special (Visual Proofs):
1. **Propositional Resolution Engine:** Checks every claim against past statements in real time. When a logical contradiction occurs, it derives the empty clause ($\bot$) and triggers a formal contradiction refutation alert.
2. **Monte Carlo Tree Search (MCTS):** Evaluates multiple candidate rebuttals per turn and selects the optimal path. The UI displays an MCTS trace ("show your work" move-list).
3. **Tactical Coaching Report:** Synthesizes high-risk vulnerabilities and pairs every attack with a concrete, domain-specific counter-reply strategy.

### Design Mandate ("Cognitive Arena" Theme)
- **NOT** generic AI sci-fi / cyberpunk neon gradients.
- **NOT** heavy default glassmorphism or bubbly rounded corners.
- **Aesthetic:** A crisp, dark, precision research board — think chess engine analysis board meets formal debate courtroom.
- **Palette:** Dark charcoal base (`#0d0f12`), cold cyan (`#38bdf8`) for Agent A, warm copper/amber (`#fbbf24`) for Agent B, acid green (`#34d399`) for valid proofs, ember red (`#f87171`) for contradiction alerts.

---

## 2. Design System & CSS Variables

Place this in `index.css` or Tailwind config:

```css
:root {
  --bg-main:       #0d0f12;
  --bg-surface:    #14181f;
  --bg-elevated:   #1a202a;
  --bg-subtle:     #11141a;

  --border:        #232b36;
  --border-strong: #333d4d;
  --border-hi:     #475569;

  --ink-primary:   #f8fafc;
  --ink-secondary: #94a3b8;
  --ink-faint:     #64748b;
  --ink-inverted:  #0f172a;

  /* Agent A: Cold Cyan / Ice Blue */
  --agent-a:       #38bdf8;
  --agent-a-dim:   rgba(56, 189, 248, 0.08);
  --agent-a-border:rgba(56, 189, 248, 0.35);

  /* Agent B: Warm Copper / Amber */
  --agent-b:       #fbbf24;
  --agent-b-dim:   rgba(251, 191, 36, 0.08);
  --agent-b-border:rgba(251, 191, 36, 0.35);

  /* Semantic Status */
  --valid:         #34d399;
  --valid-dim:     rgba(52, 211, 153, 0.1);
  --valid-border:  rgba(52, 211, 153, 0.3);

  --contra:        #f87171;
  --contra-dim:    rgba(248, 113, 113, 0.1);
  --contra-border: rgba(248, 113, 113, 0.4);

  /* Fonts */
  --serif:         'Fraunces', Georgia, serif;
  --sans:          'Inter', -apple-system, sans-serif;
  --mono:          'JetBrains Mono', Consolas, monospace;
}
```

---

## 3. TypeScript Interfaces & Data Models

Copy these interfaces into `src/types/debate.ts`:

```typescript
export interface StartDebateRequest {
  topic: string;
  max_turns?: number;
}

export interface StartDebateResponse {
  debate_id: string;
  topic: string;
  max_turns: number;
  fact_base_count: number;
  message: string;
}

export interface NextTurnRequest {
  debate_id: string;
}

export interface Claim {
  text: string;
  speaker: 'agent_a' | 'agent_b';
  turn_number: number;
  propositional_form: string; // e.g. "Exams → StressHigh"
  is_contradicted: boolean;
}

export interface ContradictionResult {
  found: boolean;
  conflicting_clauses: string[][]; // e.g. [["Exams → StressHigh", "¬StressHigh"]]
  proof_steps: string[];
}

export interface RejectedCandidate {
  text: string;
  score: number;
  visit_count: number;
}

export interface MCTSTrace {
  chosen_rebuttal: string;
  chosen_score: number;
  rejected_candidates: RejectedCandidate[];
  n_simulations: number;
}

export interface Turn {
  turn_number: number;
  claim: Claim;
  contradiction_result: ContradictionResult;
  mcts_trace?: MCTSTrace | null;
  mode?: 'live' | 'fallback';
}

export interface CorneringPoint {
  point: string;
  speaker: string; // "Agent A (Proposer)" | "Agent B (Opponent)"
  risk_level: string; // "HIGH THREAT" | "TACTICAL ADVANTAGE" | "CRITICAL VULNERABILITY"
  why_dangerous: string;
  best_reply: string;
}

export interface DebateSummary {
  debate_id: string;
  topic: string;
  total_turns: number;
  winner: string; // "Agent A (Proposer)" | "Agent B (Opponent)" | "Draw / Balanced"
  winner_reasoning: string;
  proposer_key_points: string[];
  opponent_key_points: string[];
  total_contradictions: number;
  verdict_statement: string;
  cornering_points: CorneringPoint[];
  proposer_full_arguments: string[];
  opponent_full_arguments: string[];
}

export interface DebateSession {
  debate_id: string;
  topic: string;
  max_turns: number;
  fact_base: string[];
  turns: Turn[];
  status: 'not_started' | 'running' | 'complete';
  summary?: DebateSummary | null;
}
```

---

## 4. Backend API Endpoints & Contracts

Base URL: `http://localhost:8000` (or configurable via `VITE_API_URL`)

| Endpoint | Method | Request Body | Response Model | Description |
|---|---|---|---|---|
| `/start-debate` | `POST` | `{ topic: string, max_turns?: number }` | `StartDebateResponse` | Generates fact base on-demand & returns `debate_id` |
| `/next-turn` | `POST` | `{ debate_id: string }` | `Turn` | Advances debate by 1 turn |
| `/transcript/{debate_id}` | `GET` | _None_ | `DebateSession` | Retrieves full turn history and state |
| `/summary/{debate_id}` | `GET` | _None_ | `DebateSummary` | Fetches verdict report & tactical coaching |
| `/mcts-trace/{debate_id}/{turn_number}` | `GET` | _None_ | `MCTSTrace` | Fetches MCTS candidate evaluation trace |

---

## 5. API Client Code (`src/lib/api.ts`)

Copy-pasteable production API client:

```typescript
import {
  StartDebateRequest,
  StartDebateResponse,
  Turn,
  DebateSession,
  DebateSummary,
  MCTSTrace,
} from '../types/debate';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJSON<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}`;
    try {
      const errData = await response.json();
      errorMsg = errData.detail || errData.message || errorMsg;
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

export async function startDebate(topic: string, maxTurns: number = 20): Promise<StartDebateResponse> {
  return fetchJSON<StartDebateResponse>('/start-debate', {
    method: 'POST',
    body: JSON.stringify({ topic, max_turns: maxTurns }),
  });
}

export async function nextTurn(debateId: string): Promise<Turn> {
  return fetchJSON<Turn>('/next-turn', {
    method: 'POST',
    body: JSON.stringify({ debate_id: debateId }),
  });
}

export async function getTranscript(debateId: string): Promise<DebateSession> {
  return fetchJSON<DebateSession>(`/transcript/${debateId}`);
}

export async function getDebateSummary(debateId: string): Promise<DebateSummary> {
  return fetchJSON<DebateSummary>(`/summary/${debateId}`);
}

export async function getMctsTrace(debateId: string, turnNumber: number): Promise<MCTSTrace> {
  return fetchJSON<MCTSTrace>(`/mcts-trace/${debateId}/${turnNumber}`);
}
```

---

## 6. Key Screens & UX Architecture

### Screen 1: Topic Setup (Hero Screen)
- **Derivation Typewriter Sequence:** Types 3 formal logic assertions before title animates in:
  `assert(premise_1 → conclusion)`
  `assert(¬conclusion ∨ ¬evidence)`
  `resolve(claim_1, claim_2) ⊢ ⊥`
- **Serif Title:** `Agentic Debate Arena` (`Fraunces` font, italic on *Debate*).
- **Topic Input Field:** Dark input box with 1px border.
- **Rounds Selector:** Dropdown for 6, 10, 20, 30 turns.
- **Preset Chips:** Quick-select topics:
  - `"Should AI development be globally regulated?"`
  - `"Is UBI effective against automation?"`
  - `"Should standardized exams be abolished?"`
  - `"Should social media be a public utility?"`
- **CTA Button:** `"Open the docket →"` (Shows spinner + `"Building knowledge base…"` during API call).

### Screen 2: Debate Arena (Main Timeline View)
- **Sticky Header:**
  - Topic title + Docket ID + turn progress indicator (`Turn X of N`).
  - Controls: `Next turn` (primary action), `Auto-run` (auto-advances turns every 2.5s), `Verdict` (opens modal), `↩` (Reset).
  - Theme Switcher: Segmented toggle button (`Obsidian`, `Academic`, `Terminal`).
  - Status Line: `<span className="live-dot" /> session live — gemini-3.5-flash × nemotron-3-ultra`.
- **Alternating Timeline Spine:**
  - Center vertical spine line (`1px` solid border).
  - **Left Cards (Agent A / Proposer):** Cyan accent border on left, cyan dot on spine.
  - **Right Cards (Agent B / Opponent):** Amber accent border on right, amber dot on spine.
  - **Footer Strip:** Formatted logic clause (`∴ Exams → StressHigh`) + status badge (`✓ consistent` or `⚡ contradiction`).

### Screen 3: Contradiction Alert Card
- Embedded directly in the transcript when `contradiction_result.found === true`.
- Ember red border and subtle pulse animation.
- Rotated stamp badge: `PROVEN ⚡`.
- Human-readable logic refutation explanation + formal clause syntax in monospace block:
  `Exams → StressHigh ∧ ¬StressHigh`

### Screen 4: MCTS Trace Panel
- Rendered below a turn when `mcts_trace` is present.
- Displays candidate evaluation set:
  - **Winner Card:** Highlighted with acid green border (`✓ selected · score 0.78`).
  - **Rejected Candidates:** Faded opacity with visit counts and score breakdown (`score 0.41 · 12v`).

### Screen 5: Verdict Summary Modal
- **Tab 1: Tactical Coaching & Counter-Reply Briefing:**
  - Displays high-risk attack cards landed during debate.
  - Pairs every attack with a concrete, domain-specific **counter-reply strategy**.
- **Tab 2: Logic Verdict & Theorem Analysis:**
  - Winner banner (`Agent A`, `Agent B`, or `Draw`).
  - Contradiction count stat badge.
  - Executive logic synthesis + key core points.
- **Tab 3: Full Argument Breakdown:**
  - Grid of all spoken claims made throughout the debate.

---

## 7. Single Master Prompt for Lovable AI

> Copy and paste the entire prompt box below into Lovable AI to build the complete frontend in one go:

```text
Create a modern, ultra-clean React application (Vite + Tailwind CSS + Lucide React) called "Agentic Debate Arena". 
The application visualizes two AI agents debating a topic in real time, backed by a propositional resolution engine that catches logical contradictions and a Monte Carlo Tree Search (MCTS) algorithm that selects rebuttals.

DESIGN DIRECTION ("Cognitive Arena" Theme):
- Dark obsidian base (#0d0f12 background, #14181f surfaces, #232b36 borders).
- Typography: Use 'Fraunces' serif for display titles, 'Inter' for UI/body, and 'JetBrains Mono' for logic clauses and stats.
- Agent A identity color: Cold Cyan (#38bdf8).
- Agent B identity color: Warm Copper/Amber (#fbbf24).
- Valid/Proof badge: Acid Green (#34d399).
- Contradiction alert: Ember Red (#f87171).
- Strictly AVOID generic AI sci-fi neon gradients, default glassmorphism, or bubbly childish styling. Make it look like a serious explainable reasoning tool (chess analysis board meets formal debate stage).

REQUIRED SCREENS & FEATURES:

1. TOPIC SETUP (HERO SCREEN):
- Typewriter animation printing formal logic derivation lines before title appears:
  "assert(premise_1 → conclusion)", "assert(¬conclusion ∨ ¬evidence)", "resolve(claim_1, claim_2) ⊢ ⊥"
- Title: "Agentic Debate Arena" with elegant serif typography.
- Topic Input box with turn count dropdown (6, 10, 20, 30 turns).
- Suggested preset chips ("Should AI development be globally regulated?", "Is UBI effective against automation?", etc.).
- Primary CTA button "Open the docket →" with loading state ("Building knowledge base…").

2. MAIN DEBATE ARENA:
- Sticky header containing: Docket ID, Topic title, Turn counter (Turn X of N), Progress bar, Action buttons ("Next turn", "Auto-run", "Verdict", "Reset"), and a segmented Theme Switcher ("Obsidian", "Academic", "Terminal").
- Central vertical timeline spine line.
- Left-aligned cards for Agent A (proposer) with thin cyan left border.
- Right-aligned cards for Agent B (opponent) with thin amber right border.
- Claim cards display turn text, speaker badge, and formal logic clause notation (e.g., "∴ Exams → StressHigh").

3. CONTRADICTION ALERT CARDS:
- Appears in timeline when a contradiction is derived by resolution refutation.
- Styled with ember red border, rotated "PROVEN ⚡" stamp, human explanation, and monospace clause proof (e.g. "Exams → StressHigh ∧ ¬StressHigh").

4. MCTS TRACE PANELS:
- Shows "How this rebuttal was chosen" trace below turns.
- Displays candidate cards: winner highlighted in green ("score 0.78 · selected"), rejected candidates faded with score & visit count.

5. VERDICT REPORT MODAL:
- 3 Tabs:
  - "Tactical Coaching": High-risk attacks paired with specific counter-reply strategies.
  - "Logic Verdict": Winner announcement, reasoning, total contradictions, and executive synthesis.
  - "Full Arguments": Filterable grid of all spoken claims.

BACKEND API INTEGRATION:
Use API base URL "http://localhost:8000":
- POST /start-debate body: { topic, max_turns } -> returns { debate_id, topic, max_turns, fact_base_count }
- POST /next-turn body: { debate_id } -> returns Turn object
- GET /transcript/{debate_id} -> returns full DebateSession object
- GET /summary/{debate_id} -> returns DebateSummary object
- GET /mcts-trace/{debate_id}/{turn_number} -> returns MCTSTrace object

Auto-run feature: Automatically calls POST /next-turn every 2.5 seconds when active, pausing when max_turns is reached and automatically opening the Verdict Report Modal.
```
