# UI DESIGN PROMPT — "Agentic Debate Arena" (Cognitive Arena theme)

Paste this into your React UI generator / AI coding assistant.

---

## PROMPT START

Create a premium, modern UI for my React project (Vite + Tailwind + shadcn/ui) called **"Agentic Debate Arena."** The app visualizes two AI agents debating a topic, where a propositional-resolution engine catches logical contradictions and a Monte Carlo Tree Search algorithm selects each side's best rebuttal. The UI's entire visual language must communicate one core idea: **this is explainable, provable AI reasoning — not a black-box chatbot.** Every design choice should reinforce "logic made visible," not generic sci-fi decoration.

### Design direction
- A refined, minimal "Cognitive Arena" aesthetic — technical and intentional, not noisy or template-like
- Dark theme base, smooth and immersive, strong visual hierarchy
- Elegant typography, generous whitespace, excellent spacing rhythm between all sections
- Avoid default glassmorphism, avoid generic blue-purple neon gradients, avoid cluttered sci-fi visual noise
- Should feel like a serious research/product tool (think: a chess engine analysis board crossed with a courtroom/debate stage), not a gimmicky cyberpunk concept

### Color system — meaning-driven, not decorative
- **Base**: dark charcoal / graphite / obsidian (e.g., `#0d0f12` background, `#161a1f` panel surfaces)
- **Agent A identity color**: cold cyan/ice-blue (distinct, calm)
- **Agent B identity color**: warm copper/amber (distinct, calm) — the two agents should be instantly visually distinguishable at a glance without reading labels
- **Valid/proof-verified claim**: acid green accent — used sparingly, only on claims that survive logical scrutiny
- **Contradiction detected**: ember red/orange — used as a deliberate "alert" moment, should visually stand out against the otherwise calm palette (this is your best demo beat — make it satisfying when it triggers)
- **Neutral UI chrome** (borders, dividers, inactive states): muted silver/slate greys
- Keep the palette controlled — accent colors should only appear where they carry semantic meaning (valid/contradiction/agent identity), not as general decoration

### Layout — core screens

**1. Topic Setup screen**
- Clean centered input for the debate topic
- Minimal, elegant — a single clear call-to-action ("Begin Debate"), subtle loading state while the fact base generates in the background (label this step honestly, e.g., "Building knowledge base…")

**2. Debate Arena screen (main view)**
- Two symmetric agent panels (left = Agent A / Gemini, right = Agent B / Nemotron), each showing:
  - Agent name/model badge
  - A live-scrolling stream of their claims as cards
  - A compact "knowledge base status" indicator (e.g., small dot/counter showing number of claims held, turns green if internally consistent, flashes red briefly if a contradiction was just found)
- Center column: shared transcript timeline connecting both sides turn-by-turn, like a chess move-list
- Claim cards: each claim rendered in a card styled with the owning agent's identity color as a thin left-border accent; if a claim is later contradicted, the card gets a red glow/outline treatment (subtle, not garish) plus a small "⚡ contradiction" tag

**3. Contradiction Proof Panel** (expandable/side panel, triggers when resolution finds a conflict)
- Shows the exact two (or more) conflicting clauses in clean formatted logic notation (e.g., `Exams → StressHigh` vs `¬StressHigh`)
- A short plain-English explanation beneath the formal notation
- This panel is a key novelty-demonstration moment — treat it with extra visual polish: a focused modal or slide-in panel, calm reveal animation, not abrupt

**4. MCTS Trace Panel** (expandable/side panel, shows the reasoning behind a chosen rebuttal)
- Displays the candidate rebuttals that were considered as a small horizontal set of cards, each with its simulated score
- The chosen rebuttal is highlighted (agent's identity color, subtle glow); rejected candidates shown faded/desaturated with their scores still visible
- This is your "show your work" moment for the algorithmic novelty — make the winning path visually obvious at a glance

### Visual language
- Sharp, clean panels with crisp thin borders; glow effects used only meaningfully (contradiction alerts, chosen MCTS move, active speaking agent) — not ambient decoration everywhere
- Subtle grid/data-line motifs are fine in the background chrome (very restrained), evoking "structured reasoning" rather than generic sci-fi
- Soft layered shadows between panels for depth; smooth, refined hover states on interactive elements (transcript entries, expandable panels)
- Rounded corners: modest and intentional, not overly soft/bubbly — this should feel precise, not playful
- Status/terminal-style small indicators are welcome (small dots, thin dividers, monospace turn counters) since they reinforce the "systematic reasoning" feel

### Typography
- Pair a clean, slightly technical sans-serif for UI chrome/labels with a highly readable body font for claim text
- Use monospace selectively for the formal logic notation in the Contradiction Proof Panel (this makes the logic feel literally "computed," reinforcing the explainability pitch)
- Strong, clear heading hierarchy; generous line-height on claim text since users will be reading debate arguments, not just scanning UI

### Animation and interaction
- Claims should animate in with a smooth, brief reveal (not flashy) as each turn completes
- Contradiction detection should have a distinct but tasteful "alert" animation (e.g., a brief red pulse on the conflicting cards) — this is a payoff moment, let it register
- MCTS candidate reveal can have a quick staggered fade-in for the candidate set, then a settle/highlight on the winner
- All other transitions should be smooth and restrained, supporting readability over spectacle

### Component expectations
- Reusable primitives: Card, Badge (for agent identity + status), Panel (expandable side panel), Divider, ScoreBar (for MCTS candidate scores)
- Build with shadcn/ui as the base component layer, customized with the design tokens above — should feel distinctive and purpose-built, not default shadcn styling
- Fully responsive: the two-agent side-by-side layout should gracefully stack vertically on tablet/mobile with the transcript remaining scannable

### Implementation notes
- Use React (Vite) with Tailwind CSS; define the color/spacing/radius/shadow system as CSS variables or a Tailwind theme extension so it's consistent and easy to reuse across components
- Keep the design system cohesive across every screen — Topic Setup, Debate Arena, and the two expandable panels should feel like one continuous product, not separately styled pages

### Constraints
- No default glassmorphism
- No generic blue-purple neon gradient cyberpunk look
- No decorative visual noise that doesn't carry meaning
- No cramped spacing or inconsistent padding/margins
- No generic AI-landing-page appearance — this should look like a purpose-built reasoning/analysis tool

### Overall goal
A sophisticated, dark, precision-feeling interface where color, motion, and layout are never just decorative — every visual signal (agent identity colors, the green/red validity system, the MCTS highlight-vs-faded treatment) directly represents something the underlying algorithms actually computed. The UI should make the audience *feel* the difference between "an LLM said so" and "the system proved it."

## PROMPT END
