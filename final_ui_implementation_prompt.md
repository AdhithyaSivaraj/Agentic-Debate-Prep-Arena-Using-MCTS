# FINAL UI IMPLEMENTATION PROMPT — Agentic Debate Arena

Paste this into Antigravity (recommend Gemini 3.6 Flash, Medium-High thinking — this is React/CSS implementation work against an exact visual reference, not novel design work).

---

## PROMPT START

I'm giving you a complete, working HTML/CSS/JS reference file below. This is the FINAL, approved visual design for the Agentic Debate Arena project. Your job is to reimplement this exactly as React components (per the existing `/frontend` structure in `project_structure_prompt.md`), not to redesign or reinterpret it. Treat the HTML below as a pixel-and-motion source of truth.

### Design rationale (read this so you understand *why*, not just *what*)

This design deliberately avoids generic "AI-generated" visual clichés — dark background + single neon accent, warm-cream + terracotta + serif, or hairline-broadsheet newspaper layouts. Instead:

- **Concept**: a "proof ledger / docket" aesthetic — closer to a legal transcript or mathematician's proof notebook than a SaaS dashboard. This matches the actual subject matter: formal logic, resolution proofs, and adversarial argument.
- **Signature element**: when the resolution engine catches a contradiction, an animated "PROVEN" stamp rotates and springs into place — a physical, memorable moment tied directly to what the algorithm actually computed. This should feel like the emotional payoff of the whole demo.
- **Hero moment**: before the title renders, small propositional-logic lines flicker in sequence (`assert(exams → recall_under_pressure)`...) and then resolve into the headline — literally dramatizing the resolution algorithm as the page's opening beat, instead of a generic loading spinner or "initializing..." boot text.
- **Layout**: NOT a three-panel dashboard. Claims alternate left/right along a central vertical "spine," like a courtroom transcript or git log — connected by small stem/dot connectors. This is structurally different from typical AI-dashboard templates, not just re-skinned.
- **Palette — meaning-driven, not decorative**: warm near-black background (not blue-black), cold slate for Agent A, warm brass for Agent B, oxblood reserved ONLY for contradiction moments, moss green ONLY for "proven consistent" states. Every color means something; none are ambient decoration.
- **Typography**: Fraunces (a serif with real character) for headlines and claim text, Instrument Sans for UI chrome, JetBrains Mono for logic notation and technical labels — a deliberate three-role type system, not a generic system-font stack.
- **Motion is functional, not decorative**: a living canvas-based "argument graph" background (nodes/edges drifting, representing the retrieval knowledge graph — not generic particle effects), staggered page-load reveals, real `IntersectionObserver`-driven scroll reveals for the arena section, a spring-animated contradiction stamp, and refined button micro-interactions (see below). Nothing animates without a reason.
- **Buttons specifically** — three tiers, each with a distinct hover behavior:
  - `.btn` (secondary): subtle border, a diagonal light-sweep gradient that sweeps across on hover (via `::before` + `transform: translateX`), lifts 2px, border shifts to brass.
  - `.btn.primary`: solid paper-colored fill, turns brass on hover with a soft ambient shadow (`--btn-shadow`), used for the single most important action per view (e.g. "Next turn").
  - `.btn.ghost`: near-invisible until hover, for tertiary actions (e.g. "Verdict").
  - `.cta` (hero-level call to action): larger, same light-sweep treatment, stronger lift and shadow on hover.
  - Only ONE `.btn.primary` should ever appear per view — this is a deliberate restraint rule, don't add more.
- **Theming**: this is a real light/dark system via a `data-theme` attribute on `<html>`, not two separate files. Every color is a CSS variable that flips between the `[data-theme="dark"]` and `[data-theme="light"]` blocks. The canvas graph animation reads its colors from CSS variables at runtime too (see `getRGB()` in the script), so it correctly re-themes without a page reload.
- **Cursor**: intentionally untouched — no custom cursor effects, no cursor-follow gimmicks. Standard pointer/text cursor behavior throughout.

### What you must do

1. Convert this single HTML file into proper React components matching the structure already defined in `project_structure_prompt.md` (`TopicSetup.jsx`, `DebateArena.jsx`, `AgentPanel.jsx` → adapt to the spine/card layout below, `ClaimCard.jsx`, `ContradictionAlert.jsx` → the stamp/contra-card treatment, `MCTSTracePanel.jsx` → the candidate row, `TranscriptLog.jsx`).
2. Preserve every animation, transition, and timing value exactly as written — these were deliberately tuned (easing curves, delays, stagger timing). Don't "clean up" or simplify the motion.
3. Implement the theme system as real React state (e.g. a `ThemeContext` or a simple `useState` + `data-theme` attribute on the root element), not a CSS-only toggle — it needs to be controllable from a settings/header control in the real app.
4. Reimplement the canvas argument-graph background as a proper React component (e.g. `ArgumentGraphBackground.jsx`) using a `useRef` + `useEffect` pattern for the canvas animation loop, cleaning up the `requestAnimationFrame` loop and resize listener on unmount.
5. Reimplement the derivation-line hero intro and the scroll-triggered reveals (`IntersectionObserver`) as proper React patterns (`useEffect` + refs), not direct DOM manipulation copy-pasted from the vanilla JS.
6. Wire the static/placeholder content in this reference (sample claims, sample contradiction, sample MCTS candidates) to the real data coming from the FastAPI backend endpoints already defined in `project_structure_prompt.md` — the reference file has hardcoded example content only to demonstrate the visual design.
7. Keep the exact spacing scale used below (`--sp-2` through `--sp-7`, 8/12/18/28/48/88px) as your Tailwind theme tokens or CSS variables — this fixes the alignment/spacing inconsistency issues from earlier iterations. Every component must pull from this shared scale, no one-off pixel values.
8. Google Fonts (Fraunces, Instrument Sans, JetBrains Mono) should be loaded once at the app root, not per-component.

### What NOT to do

- Do not reinterpret or "improve" the visual design — this has already been through multiple design iterations and is approved. Implement it faithfully.
- Do not revert to a dashboard/three-equal-panel layout — the spine/alternating-card layout is intentional and final.
- Do not add cursor effects of any kind.
- Do not simplify away the theme system, the canvas background, or the derivation intro sequence to save implementation time — these are the signature elements that make this design distinctive; cutting them defeats the purpose of this whole design pass.

---

### REFERENCE FILE (complete, working, open this directly in a browser to see it live before implementing)

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<title>Agentic Debate Arena</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,380;0,9..144,500;0,9..144,600;1,9..144,500&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root[data-theme="dark"]{
    --ink-0:#0e0d0b; --ink-1:#161512; --ink-2:#1e1c18;
    --line:#2c2a24; --line-strong:#42402fa8;
    --paper:#eae5d8; --paper-soft:#b3ac97; --paper-faint:#6b6858;
    --slate:#7d9bb0; --slate-dim:#1c262c;
    --brass:#d1a256; --brass-dim:#2c2415;
    --oxblood:#c65a4a; --oxblood-dim:#241412;
    --moss:#9ab26e; --moss-dim:#1d2216;
    --graph-dot: 234,229,216; --graph-line: 209,162,86;
    --btn-shadow: 0 16px 34px rgba(0,0,0,.4);
  }
  :root[data-theme="light"]{
    --ink-0:#f3f0e6; --ink-1:#fbf9f2; --ink-2:#ece8db;
    --line:#ddd7c4; --line-strong:#c3bc9f;
    --paper:#1c1a14; --paper-soft:#59543f; --paper-faint:#948d78;
    --slate:#3e5266; --slate-dim:#dde3e8;
    --brass:#8a5a1e; --brass-dim:#f1e3c8;
    --oxblood:#8f3527; --oxblood-dim:#f4ddd6;
    --moss:#51632f; --moss-dim:#e3e8d4;
    --graph-dot: 28,26,20; --graph-line: 138,90,30;
    --btn-shadow: 0 16px 34px rgba(28,26,20,.12);
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{margin:0;background:var(--ink-0);color:var(--paper);font-family:var(--sans, 'Instrument Sans', sans-serif);overflow-x:hidden;transition:background .4s ease,color .4s ease;}
  ::selection{background:var(--oxblood);color:var(--ink-0);}
  #graph{position:fixed;inset:0;z-index:0;opacity:.5;}
  .content{position:relative;z-index:1;}
  :root{
    --serif:'Fraunces', Georgia, serif;
    --sans:'Instrument Sans', -apple-system, sans-serif;
    --mono:'JetBrains Mono', Consolas, monospace;
    --sp-2:8px; --sp-3:12px; --sp-4:18px; --sp-5:28px; --sp-6:48px; --sp-7:88px;
  }

  .theme-toggle{position:fixed;top:var(--sp-5);right:var(--sp-5);z-index:5;display:flex;align-items:center;gap:8px;border:1px solid var(--line-strong);background:var(--ink-1);border-radius:100px;padding:5px;transition:all .3s ease;}
  .theme-toggle button{border:none;background:transparent;color:var(--paper-faint);font-family:var(--mono);font-size:10px;letter-spacing:.04em;text-transform:uppercase;padding:6px 12px;border-radius:100px;cursor:pointer;transition:all .25s ease;}
  .theme-toggle button.active{background:var(--paper);color:var(--ink-0);}

  .hero{min-height:100vh;display:flex;flex-direction:column;justify-content:center;padding:0 var(--sp-6);max-width:1180px;margin:0 auto;}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--paper-faint);margin-bottom:var(--sp-5);opacity:0;animation:fadeUp .7s ease .1s forwards;}
  .derive-line{font-family:var(--mono);font-size:12.5px;color:var(--paper-faint);margin-bottom:var(--sp-3);min-height:18px;opacity:0;}
  .derive-line.show{animation:flicker .5s ease forwards;}
  @keyframes flicker{0%{opacity:0;}30%{opacity:1;}55%{opacity:.2;}80%{opacity:1;}100%{opacity:.55;}}
  @keyframes fadeUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}

  h1{font-family:var(--serif);font-weight:500;font-size:clamp(48px,9vw,108px);line-height:.96;letter-spacing:-0.015em;margin:0 0 var(--sp-5);max-width:900px;opacity:0;color:var(--paper);}
  h1.reveal{animation:titleIn 1s cubic-bezier(.16,1,.3,1) forwards;}
  @keyframes titleIn{from{opacity:0;transform:translateY(28px) scale(.98);filter:blur(6px);}to{opacity:1;transform:translateY(0) scale(1);filter:blur(0);}}
  h1 em{font-style:italic;color:var(--brass);}

  .sub{font-size:16.5px;line-height:1.7;color:var(--paper-soft);max-width:480px;margin:0 0 var(--sp-6);opacity:0;animation:fadeUp .7s ease .5s forwards;}

  .docket-field{max-width:620px;border:1px solid var(--line-strong);background:var(--ink-1);border-radius:3px;padding:var(--sp-4);margin-bottom:var(--sp-5);transition:border-color .3s ease;opacity:0;animation:fadeUp .7s ease .65s forwards;}
  .docket-field:focus-within{border-color:var(--brass);}
  .field-label{font-family:var(--mono);font-size:10.5px;color:var(--paper-faint);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;}
  input[type=text]{width:100%;border:none;background:transparent;color:var(--paper);font-family:var(--serif);font-size:19px;outline:none;}
  .field-row{display:flex;justify-content:space-between;align-items:center;margin-top:var(--sp-3);padding-top:var(--sp-3);border-top:1px dashed var(--line);}
  select{border:none;background:transparent;font-family:var(--mono);font-size:12px;color:var(--paper-soft);}

  .docket-list{display:flex;flex-wrap:wrap;gap:var(--sp-2);margin-bottom:var(--sp-6);opacity:0;animation:fadeUp .7s ease .78s forwards;}
  .docket-item{border:1px solid var(--line);border-radius:100px;padding:8px 16px 8px 10px;font-size:13px;color:var(--paper-soft);cursor:pointer;transition:all .25s cubic-bezier(.16,1,.3,1);display:flex;align-items:center;gap:8px;background:var(--ink-1);}
  .docket-item .n{font-family:var(--mono);font-size:10px;color:var(--paper-faint);}
  .docket-item:hover{border-color:var(--brass);color:var(--paper);transform:translateY(-2px);}

  .btn{position:relative;border:1px solid var(--line-strong);background:var(--ink-1);color:var(--paper);border-radius:6px;padding:11px 18px;font-family:var(--sans);font-size:13px;font-weight:500;cursor:pointer;transition:transform .2s cubic-bezier(.16,1,.3,1),box-shadow .2s ease,border-color .2s ease,background .2s ease;display:inline-flex;align-items:center;gap:8px;isolation:isolate;overflow:hidden;}
  .btn::before{content:'';position:absolute;inset:0;background:linear-gradient(120deg, transparent, rgba(209,162,86,.14), transparent);transform:translateX(-120%);transition:transform .5s cubic-bezier(.16,1,.3,1);z-index:-1;}
  .btn:hover::before{transform:translateX(120%);}
  .btn:hover{border-color:var(--brass);transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,.18);}
  .btn:active{transform:translateY(0) scale(.98);}
  .btn .arrow{transition:transform .25s cubic-bezier(.16,1,.3,1);}
  .btn:hover .arrow{transform:translateX(3px);}

  .btn.primary{background:var(--paper);color:var(--ink-0);border-color:var(--paper);font-weight:600;}
  .btn.primary::before{background:linear-gradient(120deg, transparent, rgba(255,255,255,.35), transparent);}
  .btn.primary:hover{background:var(--brass);border-color:var(--brass);box-shadow:var(--btn-shadow);}

  .btn.ghost{background:transparent;border-color:transparent;padding-left:6px;padding-right:6px;}
  .btn.ghost:hover{border-color:var(--line-strong);background:var(--ink-1);}

  .cta{position:relative;background:var(--paper);color:var(--ink-0);border:none;border-radius:6px;padding:17px 38px;font-family:var(--sans);font-size:14px;font-weight:600;cursor:pointer;transition:transform .25s cubic-bezier(.16,1,.3,1),box-shadow .25s ease,background .25s ease;opacity:0;animation:fadeUp .7s ease .9s forwards;isolation:isolate;overflow:hidden;}
  .cta::before{content:'';position:absolute;inset:0;background:linear-gradient(120deg, transparent, rgba(255,255,255,.4), transparent);transform:translateX(-130%);transition:transform .6s cubic-bezier(.16,1,.3,1);z-index:-1;}
  .cta:hover::before{transform:translateX(130%);}
  .cta:hover{transform:translateY(-3px);box-shadow:var(--btn-shadow);background:var(--brass);}
  .cta:active{transform:translateY(-1px) scale(.99);}

  .foot-units{margin-top:var(--sp-6);font-family:var(--mono);font-size:10.5px;color:var(--paper-faint);opacity:0;animation:fadeUp .7s ease 1.02s forwards;}

  .scroll-cue{position:absolute;bottom:var(--sp-6);left:var(--sp-6);font-family:var(--mono);font-size:10px;color:var(--paper-faint);display:flex;align-items:center;gap:8px;opacity:0;animation:fadeUp .7s ease 1.1s forwards;}
  .scroll-cue .ln{width:22px;height:1px;background:var(--paper-faint);animation:pulseW 2s ease-in-out infinite;}
  @keyframes pulseW{0%,100%{opacity:.4;}50%{opacity:1;}}

  .arena{max-width:1180px;margin:0 auto;padding:var(--sp-7) var(--sp-6) var(--sp-7);}
  .reveal-on-scroll{opacity:0;transform:translateY(30px);transition:opacity .8s cubic-bezier(.16,1,.3,1),transform .8s cubic-bezier(.16,1,.3,1);}
  .reveal-on-scroll.in{opacity:1;transform:translateY(0);}

  .arena-head{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:var(--sp-6);gap:var(--sp-4);flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:var(--sp-5);}
  .case-no{font-family:var(--mono);font-size:11px;color:var(--paper-faint);margin-bottom:6px;}
  .case-title{font-family:var(--serif);font-size:clamp(22px,3vw,32px);font-weight:500;}
  .btn-row{display:flex;gap:var(--sp-2);}
  .live-dot{width:7px;height:7px;border-radius:50%;background:var(--oxblood);display:inline-block;margin-right:8px;animation:pulse 1.8s ease-in-out infinite;}
  @keyframes pulse{0%,100%{opacity:1;}50%{opacity:.3;}}
  .status-text{font-family:var(--mono);font-size:11px;color:var(--paper-soft);margin-bottom:var(--sp-6);}

  .spine-wrap{position:relative;}
  .spine{position:absolute;left:50%;top:0;bottom:0;width:1px;background:linear-gradient(to bottom, transparent, var(--line-strong) 4%, var(--line-strong) 96%, transparent);transform:translateX(-50%);}
  .entry{position:relative;display:grid;grid-template-columns:1fr 40px 1fr;align-items:start;margin-bottom:var(--sp-5);}
  .entry .stem{grid-column:2;display:flex;justify-content:center;padding-top:22px;}
  .stem-dot{width:9px;height:9px;border-radius:50%;border:2px solid var(--ink-0);z-index:2;}
  .entry.side-a .card{grid-column:1;justify-self:end;}
  .entry.side-b .card{grid-column:3;justify-self:start;}
  .entry.side-a .stem-dot{background:var(--slate);}
  .entry.side-b .stem-dot{background:var(--brass);}

  .card{max-width:420px;background:var(--ink-1);border:1px solid var(--line);border-radius:4px;padding:var(--sp-4);transition:transform .3s cubic-bezier(.16,1,.3,1),border-color .3s ease;}
  .card:hover{transform:translateY(-3px);}
  .card.a{border-left:2px solid var(--slate);}
  .card.a:hover{border-color:var(--slate);}
  .card.b{border-right:2px solid var(--brass);}
  .card.b:hover{border-color:var(--brass);}
  .c-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--sp-2);}
  .c-name{font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;font-weight:600;}
  .c-name.a{color:var(--slate);}
  .c-name.b{color:var(--brass);}
  .c-model{font-size:10px;color:var(--paper-faint);}
  .c-text{font-family:var(--serif);font-size:16.5px;line-height:1.55;margin:0;color:var(--paper);}
  .kb-strip{display:flex;justify-content:space-between;align-items:center;margin-top:var(--sp-3);padding-top:var(--sp-2);border-top:1px dashed var(--line);font-family:var(--mono);font-size:10px;color:var(--paper-faint);}
  .kb-strip .ok{color:var(--moss);}

  .entry.contra{grid-template-columns:1fr;justify-items:center;margin:var(--sp-6) 0;}
  .contra-card{max-width:520px;width:100%;background:var(--oxblood-dim);border:1px solid var(--oxblood);border-radius:4px;padding:var(--sp-5);position:relative;text-align:center;}
  .stamp{position:absolute;top:0;left:50%;width:150px;height:68px;border:2px solid var(--oxblood);border-radius:6px;color:var(--oxblood);font-family:var(--sans);font-weight:600;font-size:13px;letter-spacing:.08em;display:flex;align-items:center;justify-content:center;text-transform:uppercase;background:var(--ink-0);transform:translate(-50%,-50%) rotate(-8deg);}
  .contra-body{margin-top:var(--sp-4);}
  .contra-eyebrow{font-family:var(--mono);font-size:10.5px;color:var(--oxblood);text-transform:uppercase;letter-spacing:.06em;margin-bottom:var(--sp-2);}
  .contra-text{font-size:14px;line-height:1.7;color:var(--paper-soft);margin:0 0 var(--sp-3);}
  .contra-code{display:inline-block;font-family:var(--mono);font-size:12px;background:var(--ink-1);border:1px solid var(--line-strong);border-radius:3px;padding:6px 12px;color:var(--paper);}

  .mcts{margin-top:var(--sp-6);border-top:1px solid var(--line);padding-top:var(--sp-5);}
  .mcts-label{font-family:var(--mono);font-size:11px;color:var(--paper-faint);text-transform:uppercase;letter-spacing:.05em;margin-bottom:var(--sp-4);}
  .cand-row{display:flex;gap:var(--sp-3);}
  .cand{flex:1;background:var(--ink-1);border:1px solid var(--line);border-radius:4px;padding:var(--sp-3) var(--sp-4);transition:transform .25s cubic-bezier(.16,1,.3,1);}
  .cand:hover{transform:translateY(-3px);}
  .cand.win{border-color:var(--moss);background:var(--moss-dim);}
  .cand-text{font-size:13px;color:var(--paper-soft);line-height:1.55;margin-bottom:var(--sp-2);}
  .cand.win .cand-text{color:var(--paper);}
  .cand-score{font-family:var(--mono);font-size:11px;color:var(--paper-faint);}
  .cand.win .cand-score{color:var(--moss);font-weight:500;}
</style>
</head>
<body>

<div class="theme-toggle">
  <button id="btn-dark" class="active">Dark</button>
  <button id="btn-light">Light</button>
</div>

<canvas id="graph"></canvas>

<div class="content">

  <div class="hero">
    <span class="eyebrow">Logic-verified argument coaching engine</span>
    <div id="derive"></div>
    <h1 id="title">Agentic <em>Debate</em> Arena</h1>
    <p class="sub">Two autonomous debaters. A resolution engine that catches every contradiction. A search tree that picks each rebuttal on purpose — nothing said without reason.</p>

    <div class="docket-field">
      <div class="field-label">Case topic</div>
      <input type="text" value="Should standardized exams be abolished?">
      <div class="field-row">
        <span style="font-family:var(--mono);font-size:11px;color:var(--paper-faint);">Docket no. 0417</span>
        <select><option>20 turns</option></select>
      </div>
    </div>

    <div class="docket-list">
      <div class="docket-item"><span class="n">02</span>Should AI development be globally regulated?</div>
      <div class="docket-item"><span class="n">03</span>Is UBI effective against automation?</div>
      <div class="docket-item"><span class="n">04</span>Should social media be a public utility?</div>
    </div>

    <button class="cta"><span>Open the docket →</span></button>
    <div class="foot-units">Unit IV — propositional resolution · Unit III — Monte Carlo tree search · Unit II — semantic retrieval</div>
    <div class="scroll-cue"><span class="ln"></span>scroll to enter the arena</div>
  </div>

  <div class="arena">
    <div class="arena-head reveal-on-scroll">
      <div>
        <div class="case-no">Docket no. 0417 — turn 04 of 20</div>
        <div class="case-title">Should standardized exams be abolished?</div>
      </div>
      <div class="btn-row">
        <button class="btn primary">Next turn <span class="arrow">→</span></button>
        <button class="btn">Auto-run</button>
        <button class="btn ghost">Verdict</button>
      </div>
    </div>
    <div class="status-text reveal-on-scroll"><span class="live-dot"></span>session live — gemini-3.6-flash × nemotron-3-ultra</div>

    <div class="spine-wrap">
      <div class="spine"></div>

      <div class="entry side-a reveal-on-scroll">
        <div class="card a">
          <div class="c-head"><span class="c-name a">Agent A — proposer</span><span class="c-model">Gemini 3.6 Flash</span></div>
          <p class="c-text">Standardized exams measure recall under artificial time pressure, not real understanding.</p>
          <div class="kb-strip"><span>10 clauses held</span><span class="ok">✓ consistent</span></div>
        </div>
        <div class="stem"><div class="stem-dot"></div></div>
      </div>

      <div class="entry side-b reveal-on-scroll">
        <div class="stem"><div class="stem-dot"></div></div>
        <div class="card b">
          <div class="c-head"><span class="c-model">Nemotron 3 Ultra</span><span class="c-name b">Agent B — opponent</span></div>
          <p class="c-text">Removing exams removes the one standardized benchmark comparable across every school.</p>
          <div class="kb-strip"><span class="ok">✓ consistent</span><span>10 clauses held</span></div>
        </div>
      </div>

      <div class="entry contra reveal-on-scroll">
        <div class="contra-card">
          <div class="stamp">Proven ⚡</div>
          <div class="contra-body">
            <div class="contra-eyebrow">Contradiction — resolution refutation</div>
            <p class="contra-text">Agent A's turn 3 claim conflicts directly with its own turn 1 position on assessment value.</p>
            <span class="contra-code">Exams → StressHigh &nbsp;∧&nbsp; ¬StressHigh ∨ ¬HealthGood</span>
          </div>
        </div>
      </div>

      <div class="entry side-a reveal-on-scroll">
        <div class="card a">
          <div class="c-head"><span class="c-name a">Agent A — proposer</span><span class="c-model">Gemini 3.6 Flash</span></div>
          <p class="c-text">Portfolio-based assessment offers a validated alternative without the same stress cost.</p>
          <div class="kb-strip"><span>11 clauses held</span><span class="ok">✓ consistent</span></div>
        </div>
        <div class="stem"><div class="stem-dot"></div></div>
      </div>
    </div>

    <div class="mcts reveal-on-scroll">
      <div class="mcts-label">How this rebuttal was chosen — MCTS trace, turn 04</div>
      <div class="cand-row">
        <div class="cand win"><div class="cand-text">Point to portfolio-based assessment as a validated alternative.</div><div class="cand-score">score 0.78 — selected</div></div>
        <div class="cand"><div class="cand-text">Concede the stress point, pivot to a fairness argument.</div><div class="cand-score">score 0.52</div></div>
        <div class="cand"><div class="cand-text">Attack the opponent's fairness claim directly.</div><div class="cand-score">score 0.41</div></div>
      </div>
    </div>
  </div>

</div>

<script>
const root = document.documentElement;
const btnDark = document.getElementById('btn-dark');
const btnLight = document.getElementById('btn-light');
function setTheme(t){
  root.setAttribute('data-theme', t);
  btnDark.classList.toggle('active', t==='dark');
  btnLight.classList.toggle('active', t==='light');
}
btnDark.addEventListener('click', ()=>setTheme('dark'));
btnLight.addEventListener('click', ()=>setTheme('light'));

const canvas = document.getElementById('graph');
const ctx = canvas.getContext('2d');
function resize(){canvas.width=window.innerWidth;canvas.height=window.innerHeight;}
resize(); window.addEventListener('resize', resize);
const N = 46;
const nodes = Array.from({length:N}, () => ({
  x: Math.random()*canvas.width, y: Math.random()*canvas.height,
  vx: (Math.random()-0.5)*0.15, vy: (Math.random()-0.5)*0.15,
  r: Math.random()*1.4+0.8
}));
function getRGB(varName){
  return getComputedStyle(root).getPropertyValue(varName).trim();
}
function step(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const dotRGB = getRGB('--graph-dot');
  const lineRGB = getRGB('--graph-line');
  for(const n of nodes){
    n.x+=n.vx; n.y+=n.vy;
    if(n.x<0||n.x>canvas.width) n.vx*=-1;
    if(n.y<0||n.y>canvas.height) n.vy*=-1;
  }
  for(let i=0;i<N;i++){
    for(let j=i+1;j<N;j++){
      const dx=nodes[i].x-nodes[j].x, dy=nodes[i].y-nodes[j].y;
      const d=Math.sqrt(dx*dx+dy*dy);
      if(d<160){
        ctx.strokeStyle=`rgba(${lineRGB},${(1-d/160)*0.12})`;
        ctx.lineWidth=1;
        ctx.beginPath(); ctx.moveTo(nodes[i].x,nodes[i].y); ctx.lineTo(nodes[j].x,nodes[j].y); ctx.stroke();
      }
    }
  }
  for(const n of nodes){
    ctx.beginPath(); ctx.arc(n.x,n.y,n.r,0,7);
    ctx.fillStyle=`rgba(${dotRGB},0.35)`; ctx.fill();
  }
  requestAnimationFrame(step);
}
step();

const lines = [
  'assert(exams → recall_under_pressure)',
  'assert(¬recall_under_pressure → ¬mastery)',
  'resolve(claim_1, claim_2) ⊢ ...'
];
const deriveEl = document.getElementById('derive');
let i=0;
function showNext(){
  if(i>=lines.length){
    document.getElementById('title').classList.add('reveal');
    return;
  }
  const el = document.createElement('div');
  el.className='derive-line';
  el.textContent = lines[i];
  deriveEl.appendChild(el);
  requestAnimationFrame(()=>el.classList.add('show'));
  i++;
  setTimeout(showNext, 420);
}
setTimeout(showNext, 300);

const obs = new IntersectionObserver((entries)=>{
  entries.forEach(e=>{ if(e.isIntersecting) e.target.classList.add('in'); });
},{threshold:0.15});
document.querySelectorAll('.reveal-on-scroll').forEach(el=>obs.observe(el));
</script>
</body>
</html>
```

### AFTER IMPLEMENTATION

Update `PROJECT_STATE.md`: log that the UI has been finalized against this reference, note the theme system is now a real React-controlled feature (not just a design mockup), and confirm the spacing scale (`--sp-2` through `--sp-7`) is being used consistently across every component going forward.

## PROMPT END
