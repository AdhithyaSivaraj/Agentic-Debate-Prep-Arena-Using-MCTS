import React, { useState, useEffect, useLayoutEffect, useRef, useCallback } from 'react';
import { ChevronRight, Play, Pause, ArrowDownToLine, Scale, RotateCcw, AlertTriangle, Zap, Check } from 'lucide-react';
import TopicSetup from './TopicSetup';
import ThemeSwitcher from './ThemeSwitcher';
import DebateSummaryModal from './DebateSummaryModal';
import WorkingOverlay from './WorkingOverlay';
import StatusRing from './StatusRing';
import { startDebate, nextTurn, getTranscript, getDebateSummary } from '../lib/api';
import { formatModelName } from '../lib/models';


// Points come only from resolution proofs: a refutation scores for the speaker,
// a self-contradiction scores for the other side.
function scoreOf(turns) {
  const s = { aRefutes: 0, aSelf: 0, bRefutes: 0, bSelf: 0 };
  for (const t of turns) {
    const isA = t.claim.speaker === 'agent_a';
    if (t.claim.refutes_opponent) s[isA ? 'aRefutes' : 'bRefutes'] += 1;
    if (t.claim.is_contradicted) s[isA ? 'aSelf' : 'bSelf'] += 1;
  }
  s.a = s.aRefutes + s.bSelf;
  s.b = s.bRefutes + s.aSelf;
  s.net = s.a - s.b;
  return s;
}


function Scoreboard({ turns }) {
  const s = scoreOf(turns);
  const position = 50 + Math.max(-46, Math.min(46, s.net * 12));
  const net = s.net === 0 ? 'even' : s.net > 0 ? `A +${s.net}` : `B +${-s.net}`;
  return (
    <div className="scoreboard" title="Refutations proven by resolution (self-contradictions count for the other side)">
      <span className="side a">A · {s.aRefutes} refuted{s.aSelf ? ` · ${s.aSelf} self` : ''}</span>
      <div className="scorebar" aria-hidden="true">
        <span className="fill-a" style={{ width: `${position}%` }} />
        <span className="fill-b" style={{ width: `${100 - position}%` }} />
        <span className="mid" />
      </div>
      <span className="side b">B · {s.bRefutes} refuted{s.bSelf ? ` · ${s.bSelf} self` : ''}</span>
      <span className="score-net">{net}</span>
    </div>
  );
}


function TurnBadges({ turn, onJump }) {
  const { is_contradicted: self, refutes_opponent: refutes, refutes_turn: target } = turn.claim;
  return (
    <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
      {turn.mode === 'fallback' && (
        <span className="badge-status muted" title="LLM unavailable: candidates came from the generated fact base">fallback</span>
      )}
      {self && <span className="badge-status contra"><AlertTriangle size={11} /> self-contradiction</span>}
      {refutes && target && (
        <button className="refute-link" onClick={() => onJump(target)} title={`Jump to turn ${target}`}>
          <Zap size={11} /> refutes turn {target}
        </button>
      )}
      {refutes && !target && <span className="badge-status refute"><Zap size={11} /> refutes opponent</span>}
      {!self && !refutes && <span className="badge-status valid"><Check size={11} /> consistent</span>}
    </span>
  );
}


function ClaimEntry({ turn, isLatest, modelName, registerRow, onJump, onHover, flash, linked }) {
  const isA = turn.claim.speaker === 'agent_a';
  const agent = isA ? 'a' : 'b';
  const fullText = turn.claim.text || '';

  const [ringState, setRingState] = useState(() => (isLatest ? 'thinking' : 'done'));
  const [shown, setShown] = useState(() => (isLatest ? 0 : fullText.length));
  const ringLg = useRef(null);
  const ringSm = useRef(null);

  // Brief typewriter for the newest claim (about one second, independent of length).
  useEffect(() => {
    if (!isLatest) {
      setRingState('done');
      setShown(fullText.length);
      return;
    }
    let alive = true;
    let typer;
    setRingState('thinking');
    setShown(0);
    const step = Math.max(1, Math.ceil(fullText.length / 65));
    const start = setTimeout(() => {
      if (!alive) return;
      setRingState('speaking');
      let n = 0;
      typer = setInterval(() => {
        n = Math.min(fullText.length, n + step);
        setShown(n);
        if (n % (step * 6) === 0) { ringLg.current?.pulse(); ringSm.current?.pulse(); }
        if (n >= fullText.length) {
          clearInterval(typer);
          setTimeout(() => alive && setRingState('done'), 150);
        }
      }, 16);
    }, 250);
    return () => { alive = false; clearTimeout(start); clearInterval(typer); };
  }, [fullText, isLatest]);

  const done = ringState === 'done';
  return (
    <div
      className="turn-row"
      data-agent={agent}
      id={`turn-${turn.turn_number}`}
      ref={el => registerRow(turn.turn_number, el)}
      onMouseEnter={() => onHover(turn.turn_number)}
      onMouseLeave={() => onHover(null)}
    >
      <div className="card-slot">
        <article className={`turn-card ${flash ? 'flash' : ''} ${linked ? 'linked' : ''}`} data-agent={agent} data-state={ringState}>
          <header className="turn-head">
            <div className="turn-who">
              <StatusRing ref={ringLg} size="lg" state={ringState} agent={agent} />
              <span className={isA ? 'badge-agent-a' : 'badge-agent-b'}>
                {isA ? 'A · Proposer' : 'B · Opponent'} <span style={{ color: 'var(--ink-faint)' }}>#{turn.turn_number}</span>
              </span>
            </div>
            <span className="turn-model">{formatModelName(modelName)}</span>
          </header>
          <p className="turn-text">
            {fullText.slice(0, shown)}
            {ringState === 'speaking' && <span className="cursor" />}
          </p>
          {done && (
            <footer className="turn-foot">
              <span className="turn-form">
                {turn.claim.issue && <span className="issue-tag">{turn.claim.issue}</span>}
                ∴ {turn.claim.propositional_form}
              </span>
              <TurnBadges turn={turn} onJump={onJump} />
            </footer>
          )}
        </article>
      </div>
      <div className="node">
        <StatusRing ref={ringSm} size="sm" state={ringState} agent={agent} />
      </div>
    </div>
  );
}


function JumpLink({ n, onJump }) {
  return (
    <button onClick={() => onJump(n)} style={{ background: 'none', border: 'none', padding: 0, color: 'inherit', textDecoration: 'underline', cursor: 'pointer', font: 'inherit' }}>
      turn {n}
    </button>
  );
}


function ProofEntry({ turn, onJump }) {
  const isSelf = turn.claim.is_contradicted;
  const result = isSelf ? turn.contradiction_result : turn.clash_result;
  const pair = result?.conflicting_clauses?.[0];
  const target = isSelf ? turn.claim.contradicts_turn : turn.claim.refutes_turn;
  const speakerColor = turn.claim.speaker === 'agent_a' ? 'var(--agent-a)' : 'var(--agent-b)';
  return (
    <div className="proof-row">
      <div className={`contra-card ${isSelf ? '' : 'refutation'}`} style={{ '--speaker-color': speakerColor }}>
        <div className="contra-stamp">{isSelf ? 'Self-contradiction' : 'Refuted'}</div>
        <div className="proof-label">Resolution proof · turn {turn.turn_number}</div>
        <p style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--ink-secondary)', margin: '0 0 14px' }}>
          {isSelf
            ? <>This claim contradicts the speaker's own position{target ? <> from <JumpLink n={target} onJump={onJump} /></> : ''}.</>
            : <>This claim contradicts what the opponent argued{target ? <> in <JumpLink n={target} onJump={onJump} /></> : ''}, read together with their evidence.</>}
          {' '}Resolution derived the empty clause (⊥).
        </p>
        {pair && <span className="logic-code">{pair[0]} &nbsp;+&nbsp; {pair[1]} &nbsp;⊢&nbsp; ⊥</span>}
      </div>
    </div>
  );
}


function MctsEntry({ trace, turnNumber }) {
  if (!trace) return null;
  const rows = [
    { text: trace.chosen_rebuttal, form: trace.chosen_propositional_form, score: trace.chosen_score, visits: trace.chosen_visits, winner: true },
    ...(trace.rejected_candidates || []).map(c => ({ text: c.text, form: c.propositional_form, score: c.score, visits: c.visit_count })),
  ];
  const scores = rows.map(r => r.score);
  const lo = Math.min(...scores, 0);
  const hi = Math.max(...scores, lo + 1);
  return (
    <details className="mcts">
      <summary>
        <ChevronRight size={12} className="chev" />
        How turn {turnNumber} was chosen — MCTS over {rows.length} candidates, {trace.n_simulations} simulations
      </summary>
      <div className="mcts-rows">
        {rows.map((r, i) => (
          <div key={i} className={`mcts-row ${r.winner ? 'winner' : ''}`}>
            <div>
              {r.text}
              {r.form && <span className="form">∴ {r.form}</span>}
            </div>
            <div className="mcts-bar"><span style={{ width: `${((r.score - lo) / (hi - lo)) * 100}%` }} /></div>
            <div className="mcts-num">{r.score.toFixed(2)}<br /><span style={{ color: 'var(--ink-faint)' }}>{r.visits}v</span></div>
          </div>
        ))}
      </div>
    </details>
  );
}


// Bracket arcs on the spine, from each refutation (or self-contradiction) to the turn it targets.
function LinkArcs({ turns, rowsRef, containerRef, hovered }) {
  const [paths, setPaths] = useState([]);

  const measure = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    const x = container.clientWidth / 2;
    const yOf = n => {
      const row = rowsRef.current.get(n);
      return row ? row.offsetTop + 28 : null;
    };
    const next = [];
    for (const t of turns) {
      const isA = t.claim.speaker === 'agent_a';
      const target = t.claim.refutes_opponent ? t.claim.refutes_turn : t.claim.is_contradicted ? t.claim.contradicts_turn : null;
      if (!target) continue;
      const y1 = yOf(t.turn_number);
      const y2 = yOf(target);
      if (y1 == null || y2 == null) continue;
      const dx = (isA ? -1 : 1) * Math.min(30, 14 + (y1 - y2) / 60);
      next.push({
        key: `${t.turn_number}-${target}`,
        from: t.turn_number,
        to: target,
        d: `M ${x} ${y1} C ${x + dx * 1.6} ${y1}, ${x + dx * 1.6} ${y2}, ${x} ${y2}`,
        end: { x, y: y2 },
        len: Math.abs(y1 - y2) + Math.abs(dx) * 4,
        color: t.claim.is_contradicted ? 'var(--contra)' : isA ? 'var(--agent-a)' : 'var(--agent-b)',
      });
    }
    setPaths(next);
  }, [turns, rowsRef, containerRef]);

  useLayoutEffect(() => {
    measure();
    const observer = new ResizeObserver(measure);
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [measure, containerRef]);

  return (
    <svg className="arcs" aria-hidden="true">
      {paths.map(p => {
        const state = hovered == null ? '' : hovered === p.from || hovered === p.to ? 'hot' : 'dim';
        return (
          <g key={p.key}>
            <path d={p.d} className={state} stroke={p.color} style={{ '--len': p.len }} />
            <circle cx={p.end.x} cy={p.end.y} r={state === 'hot' ? 5 : 3.5} fill={p.color} opacity={state === 'dim' ? 0.2 : 0.9} />
          </g>
        );
      })}
    </svg>
  );
}


export default function DebateArena() {
  const [session,            setSession]            = useState(null);
  const [isLoading,          setIsLoading]          = useState(false);
  const [isNextTurnLoading,  setIsNextTurnLoading]  = useState(false);
  const [isSummarizing,      setIsSummarizing]      = useState(false);
  const [summarizeCountdown, setSummarizeCountdown] = useState(0);
  const [pending,            setPending]            = useState(null);
  const [autoPlay,           setAutoPlay]           = useState(false);
  const [autoScroll,         setAutoScroll]         = useState(true);
  const [activeSummary,      setActiveSummary]      = useState(null);
  const [hovered,            setHovered]            = useState(null);
  const [flashTurn,          setFlashTurn]          = useState(null);

  const autoPlayRef = useRef(false);
  const rowsRef     = useRef(new Map());
  const timelineRef = useRef(null);

  const turns    = session?.turns || [];
  const maxTurns = session?.max_turns || 20;

  const registerRow = useCallback((n, el) => {
    if (el) rowsRef.current.set(n, el); else rowsRef.current.delete(n);
  }, []);

  const jumpTo = useCallback(n => {
    const row = rowsRef.current.get(n);
    if (!row) return;
    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setFlashTurn(n);
    setTimeout(() => setFlashTurn(f => (f === n ? null : f)), 1500);
  }, []);

  // Keep the newest turn in view.
  useEffect(() => {
    if (!autoScroll || turns.length === 0) return;
    rowsRef.current.get(turns[turns.length - 1].turn_number)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [turns.length, autoScroll]);

  // Short pause after the final turn so the closing claim can be read.
  useEffect(() => {
    if (summarizeCountdown <= 0) return;
    const t = setTimeout(() => {
      if (summarizeCountdown === 1) {
        setSummarizeCountdown(0);
        handleFetchSummary();
      } else {
        setSummarizeCountdown(c => c - 1);
      }
    }, 1000);
    return () => clearTimeout(t);
  }, [summarizeCountdown]);

  // Auto-run.
  useEffect(() => {
    autoPlayRef.current = autoPlay;
    if (!autoPlay || !session || isNextTurnLoading || activeSummary || isSummarizing) return;
    const finished = turns.length >= maxTurns || session.status === 'complete';
    const timer = setTimeout(() => {
      if (finished) {
        setAutoPlay(false);
        handleFetchSummary();
      } else if (autoPlayRef.current) {
        handleNextTurn();
      }
    }, finished ? 1200 : 2200);
    return () => clearTimeout(timer);
  }, [autoPlay, session, isNextTurnLoading, activeSummary, isSummarizing]);

  const handleStartDebate = async (topic, max, proposerModel, opponentModel) => {
    setPending({ topic, proposerModel, opponentModel });
    setIsLoading(true);
    try {
      const res = await startDebate(topic, max, proposerModel, opponentModel);
      setSession(await getTranscript(res.debate_id));
    } catch (err) {
      alert(`Failed to start debate: ${err.message}`);
    } finally {
      setIsLoading(false);
      setPending(null);
    }
  };

  const handleNextTurn = async () => {
    if (!session || isNextTurnLoading || isSummarizing || activeSummary || session.status === 'complete') return;
    if (turns.length >= maxTurns) {
      setAutoPlay(false);
      handleFetchSummary();
      return;
    }
    setIsNextTurnLoading(true);
    try {
      await nextTurn(session.debate_id);
      const updated = await getTranscript(session.debate_id);
      setSession(updated);
      if ((updated.turns || []).length >= maxTurns || updated.status === 'complete') {
        setAutoPlay(false);
        setSummarizeCountdown(4);
      }
    } catch (err) {
      alert(`Failed to advance turn: ${err.message}`);
      setAutoPlay(false);
    } finally {
      setIsNextTurnLoading(false);
    }
  };

  const handleFetchSummary = async () => {
    setSummarizeCountdown(0);
    setAutoPlay(false);
    const id = session?.debate_id;
    if (!id) return;
    setIsSummarizing(true);
    try {
      const data = await getDebateSummary(id);
      setActiveSummary(data);
      setSession(await getTranscript(id));
    } catch (err) {
      alert(`Failed to load summary: ${err.message}`);
    } finally {
      setIsSummarizing(false);
    }
  };

  const handleReset = () => {
    setAutoPlay(false);
    setSummarizeCountdown(0);
    setIsSummarizing(false);
    setSession(null);
    setActiveSummary(null);
    rowsRef.current.clear();
  };

  if (!session) {
    return (
      <div className="anim-page-enter">
        <TopicSetup onStartDebate={handleStartDebate} isLoading={isLoading} />
        {pending && (
          <WorkingOverlay
            kicker="Opening the docket"
            title="Building the fact base"
            topic={pending.topic}
            now="Framing the two sides, then generating ~20 facts with logical forms"
            note={`Agent A: ${formatModelName(pending.proposerModel)} · Agent B: ${formatModelName(pending.opponentModel)}. Each side's facts then seed its knowledge base. Usually 5–25 s.`}
          />
        )}
      </div>
    );
  }

  const isComplete = turns.length >= maxTurns || session.status === 'complete';
  const linkedTo = new Set();
  if (hovered != null) {
    for (const t of turns) {
      const target = t.claim.refutes_turn ?? t.claim.contradicts_turn;
      if (!target) continue;
      if (t.turn_number === hovered) linkedTo.add(target);
      if (target === hovered) linkedTo.add(t.turn_number);
    }
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <header className="arena-header">
        <div className="arena-header-inner">
          <div>
            <div className="arena-meta">Turn {turns.length} of {maxTurns}{isComplete ? ' · complete' : ''}</div>
            <div className="arena-topic">{session.topic}</div>
            {session.proposer_position && (
              <div className="arena-positions">
                <span className="pos a"><b>A</b> {session.proposer_position}</span>
                <span className="pos b"><b>B</b> {session.opponent_position}</span>
              </div>
            )}
          </div>
          <div className="arena-actions">
            <button id="next-turn-btn" className="btn-action" onClick={handleNextTurn} disabled={isNextTurnLoading || isComplete}>
              {isNextTurnLoading ? 'Reasoning…' : 'Next turn'} <ChevronRight size={15} />
            </button>
            <button id="autoplay-btn" className={`btn-icon ${autoPlay ? 'active' : ''}`} onClick={() => setAutoPlay(p => !p)} disabled={isComplete} title={autoPlay ? 'Pause auto-run' : 'Auto-run'}>
              {autoPlay ? <Pause size={15} /> : <Play size={15} />}
            </button>
            <button id="autoscroll-btn" className={`btn-icon ${autoScroll ? 'active' : ''}`} onClick={() => setAutoScroll(p => !p)} title={`Follow newest turn: ${autoScroll ? 'on' : 'off'}`}>
              <ArrowDownToLine size={15} />
            </button>
            <button
              id="verdict-btn"
              className={`btn-outline ${isComplete ? 'active' : ''}`}
              onClick={() => (session.summary ? setActiveSummary(session.summary) : handleFetchSummary())}
              disabled={isSummarizing}
            >
              <Scale size={14} /> {isSummarizing ? 'Writing…' : 'Verdict'}
            </button>
            <button id="reset-btn" className="btn-icon" onClick={handleReset} title="New debate">
              <RotateCcw size={15} />
            </button>
          </div>
        </div>
        <div className="arena-subbar">
          <span><span className="live-dot" />{formatModelName(session.proposer_model)} vs {formatModelName(session.opponent_model)}</span>
          <Scoreboard turns={turns} />
          <ThemeSwitcher />
        </div>
      </header>

      <main style={{ maxWidth: 1180, margin: '0 auto', padding: 'clamp(32px, 6vw, 64px) clamp(16px, 4vw, 48px) 96px' }}>
        {turns.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '120px 0', color: 'var(--ink-faint)', fontFamily: 'var(--mono)', fontSize: 12 }}>
            {session.fact_base?.length || 0} facts loaded. Press “Next turn” to hear the Proposer's opening.
          </div>
        ) : (
          <div className="timeline" ref={timelineRef}>
            <div className="timeline-spine" />
            <LinkArcs turns={turns} rowsRef={rowsRef} containerRef={timelineRef} hovered={hovered} />
            {turns.map((turn, idx) => (
              <React.Fragment key={turn.turn_number}>
                <ClaimEntry
                  turn={turn}
                  isLatest={idx === turns.length - 1}
                  modelName={turn.claim.speaker === 'agent_a' ? session.proposer_model : session.opponent_model}
                  registerRow={registerRow}
                  onJump={jumpTo}
                  onHover={setHovered}
                  flash={flashTurn === turn.turn_number}
                  linked={linkedTo.has(turn.turn_number)}
                />
                {(turn.claim.refutes_opponent || turn.claim.is_contradicted) && <ProofEntry turn={turn} onJump={jumpTo} />}
                <MctsEntry trace={turn.mcts_trace} turnNumber={turn.turn_number} />
              </React.Fragment>
            ))}

            {isComplete && !session.summary && !isSummarizing && (
              <div className="working" style={{ margin: '40px auto 0', textAlign: 'center', position: 'relative', zIndex: 1 }}>
                <div className="working-kicker">All {maxTurns} turns argued</div>
                <div className="working-title" style={{ fontSize: 22 }}>The prover has scored the debate.</div>
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 14, flexWrap: 'wrap', marginTop: 14 }}>
                  <button className="btn-action" onClick={handleFetchSummary}>
                    <Scale size={14} /> Write the verdict
                  </button>
                  {summarizeCountdown > 0 && (
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 11.5, color: 'var(--ink-faint)' }}>
                      starting in {summarizeCountdown}s…
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {isSummarizing && !activeSummary && (
        <WorkingOverlay
          kicker="Debate concluded"
          title="Writing the verdict"
          topic={session.topic}
          now={`${formatModelName(session.proposer_model)} is writing the debrief`}
          note="The winner is already decided by the resolution proofs. This step adds the written analysis and the coaching notes."
        />
      )}

      {activeSummary && <DebateSummaryModal summary={activeSummary} onClose={() => setActiveSummary(null)} />}
    </div>
  );
}
