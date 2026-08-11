import React, { useState, useEffect, useRef } from 'react';
import ArgumentGraph from './ArgumentGraph';
import TopicSetup from './TopicSetup';
import DebateSummaryModal from './DebateSummaryModal';
import StatusRing from './StatusRing';
import { startDebate, nextTurn, getTranscript, getDebateSummary } from '../lib/api';

/* ── Scroll-reveal hook ─────────────────────────────── */
function useRevealOnScroll() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in'); }),
      { threshold: 0.12 }
    );
    const els = document.querySelectorAll('.reveal-item');
    els.forEach(el => observer.observe(el));
    return () => observer.disconnect();
  });
}

function formatModelName(modelStr) {
  if (!modelStr) return 'AI Agent';
  if (modelStr.includes('versatile')) return 'Llama 3.3 70B (Groq LPU)';
  if (modelStr.includes('instant')) return 'Llama 3.1 8B (Groq LPU)';
  if (modelStr.includes('llama-3.1-8b')) return 'Llama 3.1 8B (NVIDIA)';
  if (modelStr.includes('nemotron-super-49b')) return 'Nemotron Super 49B (NVIDIA)';
  if (modelStr.includes('llama-3.3')) return 'Llama 3.3 70B (NVIDIA)';
  if (modelStr.includes('llama-3.1-70b')) return 'Llama 3.1 70B (NVIDIA)';
  if (modelStr.includes('deepseek')) return 'DeepSeek R1 (NVIDIA)';
  if (modelStr.includes('3.6')) return 'Gemini 3.6 Flash';
  if (modelStr.includes('3.5')) return 'Gemini 3.5 Flash';
  if (modelStr.includes('3.1')) return 'Gemini 3.1 Flash Lite';
  return modelStr.split('/').pop();
}

/* ── Claim Entry Component ──────────────────── */
function ClaimEntry({ turn, isAgentA, isLatest = false, modelName = '', entryRef = null, autoScroll = true }) {
  const contradicted = turn.contradiction_result?.found;
  const propForm     = turn.claim?.propositional_form;

  const [ringState, setRingState] = useState(() => (isLatest ? 'thinking' : 'done'));
  const [displayedText, setDisplayedText] = useState(() => (isLatest ? '' : turn.claim.text));
  const [showMeta, setShowMeta] = useState(() => !isLatest);

  const ringRefLg = useRef(null);
  const ringRefSm = useRef(null);

  const pulseBothRings = () => {
    ringRefLg.current?.pulse();
    ringRefSm.current?.pulse();
  };

  // ResizeObserver to lock expanding card in vertical center of viewport
  useEffect(() => {
    if (!isLatest || !autoScroll || !entryRef?.current) return;

    const element = entryRef.current;
    const observer = new ResizeObserver(() => {
      element.scrollIntoView({ behavior: 'auto', block: 'center' });
    });

    observer.observe(element);
    element.scrollIntoView({ behavior: 'auto', block: 'center' });

    return () => observer.disconnect();
  }, [isLatest, autoScroll, entryRef]);

  useEffect(() => {
    if (!isLatest) {
      setRingState('done');
      setDisplayedText(turn.claim.text);
      setShowMeta(true);
      return;
    }

    let isMounted = true;
    let charIdx = 0;
    const fullText = turn.claim.text || '';
    const stepDelay = Math.max(12, Math.min(22, Math.floor(2200 / (fullText.length || 1))));

    // 1. Start thinking for 400ms
    setRingState('thinking');
    setShowMeta(false);

    const thinkingTimer = setTimeout(() => {
      if (!isMounted) return;

      // 2. Flip to speaking & start fluid letter-by-letter text streaming
      setRingState('speaking');

      const typeInterval = setInterval(() => {
        if (!isMounted) {
          clearInterval(typeInterval);
          return;
        }

        charIdx += 1;
        setDisplayedText(fullText.substring(0, charIdx));

        if (charIdx % 8 === 0 || charIdx >= fullText.length) {
          pulseBothRings();
        }

        if (charIdx >= fullText.length) {
          clearInterval(typeInterval);

          // 3. Flip to done when typing completes
          setTimeout(() => {
            if (isMounted) {
              setRingState('done');
              setShowMeta(true);
            }
          }, 200);
        }
      }, stepDelay);
    }, 400);

    return () => {
      isMounted = false;
      clearTimeout(thinkingTimer);
    };
  }, [turn.claim.text, isLatest]);

  return (
    <div
      ref={entryRef}
      className="reveal-item in"
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 40px 1fr',
        alignItems: 'start',
        marginBottom: 28,
        scrollMarginTop: '160px',
      }}
    >
      {isAgentA ? (
        <>
          {/* Agent A Card (Left) */}
          <div style={{ gridColumn: 1, justifySelf: 'end' }}>
            <div className="turn-frame" data-agent="a" data-state={ringState}>
              <div className="turn-panel">
                <div className="card-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <StatusRing ref={ringRefLg} size="lg" state={ringState} agent="a" />
                    <span className="who badge-agent-a">Agent A — Proposer</span>
                  </div>
                  <span style={{ fontSize: 10, color: 'var(--ink-faint)', fontFamily: 'var(--mono)' }}>
                    {formatModelName(modelName)}
                  </span>
                </div>
                <p style={{
                  fontFamily: 'var(--serif)',
                  fontSize: 16,
                  lineHeight: 1.55,
                  margin: 0,
                  color: contradicted ? 'var(--contra)' : 'var(--ink-primary)',
                }}>
                  {displayedText}
                  {ringState === 'speaking' && (
                    <span style={{ display: 'inline-block', width: 2, height: 16, backgroundColor: 'var(--agent-a)', marginLeft: 2, animation: 'livePulse 0.6s infinite' }} />
                  )}
                </p>
                {showMeta && (
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: 12,
                    paddingTop: 8,
                    borderTop: '1px dashed var(--border)',
                    fontFamily: 'var(--mono)',
                    fontSize: 10,
                    animation: 'fadeUp 0.3s ease forwards',
                  }}>
                    {propForm && (
                      <span style={{ color: 'var(--ink-faint)' }}>∴ {propForm}</span>
                    )}
                    <span className={`badge-status ${contradicted ? 'contra' : 'valid'}`}>
                      {contradicted ? '⚡ contradiction' : '✓ consistent'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Spine Ring (sm) replacing .turn-node */}
          <div style={{ gridColumn: 2, display: 'flex', justifyContent: 'center', paddingTop: 22, position: 'relative', zIndex: 2 }}>
            <StatusRing ref={ringRefSm} size="sm" state={ringState} agent="a" className="turn-node" />
          </div>
          <div style={{ gridColumn: 3 }} />
        </>
      ) : (
        <>
          {/* Agent B Card (Right) */}
          <div style={{ gridColumn: 1 }} />
          {/* Spine Ring (sm) replacing .turn-node */}
          <div style={{ gridColumn: 2, display: 'flex', justifyContent: 'center', paddingTop: 22, position: 'relative', zIndex: 2 }}>
            <StatusRing ref={ringRefSm} size="sm" state={ringState} agent="b" className="turn-node" />
          </div>
          <div style={{ gridColumn: 3, justifySelf: 'start' }}>
            <div className="turn-frame" data-agent="b" data-state={ringState}>
              <div className="turn-panel">
                <div className="card-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <StatusRing ref={ringRefLg} size="lg" state={ringState} agent="b" />
                    <span className="who badge-agent-b">Agent B — Opponent</span>
                  </div>
                  <span style={{ fontSize: 10, color: 'var(--ink-faint)', fontFamily: 'var(--mono)' }}>
                    {formatModelName(modelName)}
                  </span>
                </div>
                <p style={{
                  fontFamily: 'var(--serif)',
                  fontSize: 16,
                  lineHeight: 1.55,
                  margin: 0,
                  color: contradicted ? 'var(--contra)' : 'var(--ink-primary)',
                }}>
                  {displayedText}
                  {ringState === 'speaking' && (
                    <span style={{ display: 'inline-block', width: 2, height: 16, backgroundColor: 'var(--agent-b)', marginLeft: 2, animation: 'livePulse 0.6s infinite' }} />
                  )}
                </p>
                {showMeta && (
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: 12,
                    paddingTop: 8,
                    borderTop: '1px dashed var(--border)',
                    fontFamily: 'var(--mono)',
                    fontSize: 10,
                    animation: 'fadeUp 0.3s ease forwards',
                  }}>
                    <span className={`badge-status ${contradicted ? 'contra' : 'valid'}`}>
                      {contradicted ? '⚡ contradiction' : '✓ consistent'}
                    </span>
                    {propForm && (
                      <span style={{ color: 'var(--ink-faint)' }}>∴ {propForm}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ── Contradiction Entry Component ──────────────────── */
function ContraEntry({ turn }) {
  const pairs = turn.contradiction_result?.conflicting_clauses || [];
  return (
    <div
      className="reveal-item"
      style={{ display: 'grid', gridTemplateColumns: '1fr', justifyItems: 'center', margin: '48px 0' }}
    >
      <div className="contra-card" style={{ maxWidth: 520, width: '100%', textAlign: 'center' }}>
        <div className="contra-stamp">Proven ⚡</div>
        <div style={{ marginTop: 20 }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--contra)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            Contradiction — resolution refutation
          </div>
          <p style={{ fontSize: 13.5, lineHeight: 1.65, color: 'var(--ink-secondary)', margin: '0 0 14px' }}>
            This claim conflicts directly with an earlier position held in the knowledge base.
            The resolution algorithm derived the empty clause (⊥) — a formal proof of contradiction.
          </p>
          {pairs[0] && (
            <span className="logic-code">
              {pairs[0][0]} &nbsp;∧&nbsp; {pairs[0][1]}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── MCTS Trace Entry Component ─────────────────────── */
function MctsEntry({ mctsTrace, turnNumber }) {
  if (!mctsTrace) return null;
  const chosen   = mctsTrace.chosen_rebuttal;
  const rejected = mctsTrace.rejected_candidates || [];
  const nSims    = mctsTrace.n_simulations || 10;

  return (
    <div
      className="reveal-item"
      style={{ marginTop: 28, borderTop: '1px solid var(--border)', paddingTop: 20, marginBottom: 28 }}
    >
      <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink-faint)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 14 }}>
        How this rebuttal was chosen — MCTS trace, turn {turnNumber} ({nSims} simulations)
      </div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {/* Selected Rebuttal */}
        <div className="mcts-cand winner">
          <div style={{ fontSize: 13, color: 'var(--ink-primary)', lineHeight: 1.55, marginBottom: 6 }}>{chosen}</div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--valid)', fontWeight: 600 }}>
            score 0.78 — selected (highest visits)
          </div>
        </div>
        {/* Rejected candidates */}
        {rejected.map((c, i) => (
          <div key={i} className="mcts-cand" style={{ opacity: 0.5 }}>
            <div style={{ fontSize: 13, color: 'var(--ink-secondary)', lineHeight: 1.55, marginBottom: 6 }}>{c.text}</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--ink-faint)' }}>
              score {c.score} · {c.visit_count}v
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main Arena Component ───────────────────────────── */
export default function DebateArena() {
  const [session,           setSession]           = useState(null);
  const [isLoading,         setIsLoading]         = useState(false);
  const [isNextTurnLoading, setIsNextTurnLoading] = useState(false);
  const [autoPlay,          setAutoPlay]          = useState(false);
  const [autoScroll,        setAutoScroll]        = useState(true);
  const [activeSummary,     setActiveSummary]     = useState(null);
  const [showSetup,         setShowSetup]         = useState(true);

  // Synchronous ref to track autoPlay state in real-time without closure lag
  const autoPlayRef = useRef(false);
  const lastTurnRef = useRef(null);

  useRevealOnScroll();

  /* Auto-scroll effect */
  useEffect(() => {
    if (autoScroll && lastTurnRef.current && session?.turns?.length > 0) {
      lastTurnRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [session?.turns?.length, autoScroll]);

  /* Auto-play effect */
  useEffect(() => {
    autoPlayRef.current = autoPlay;
    let timer;

    if (autoPlay && session && !isNextTurnLoading && !activeSummary) {
      const maxTurns = session.max_turns || 20;
      if ((session.turns || []).length >= maxTurns || session.status === 'complete') {
        autoPlayRef.current = false;
        setAutoPlay(false);
        handleFetchSummary();
      } else {
        timer = setTimeout(() => {
          if (autoPlayRef.current) {
            handleNextTurn();
          }
        }, 2500);
      }
    }

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [autoPlay, session, isNextTurnLoading, activeSummary]);

  const toggleAutoPlay = () => {
    setAutoPlay(prev => {
      const next = !prev;
      autoPlayRef.current = next;
      return next;
    });
  };

  const handleStartDebate = async (topic, maxTurns = 20, proposerModel, opponentModel) => {
    setIsLoading(true);
    try {
      const res      = await startDebate(topic, maxTurns, proposerModel, opponentModel);
      const sessData = await getTranscript(res.debate_id);
      setSession(sessData);
      setShowSetup(false);
    } catch (err) {
      alert(`Failed to start debate: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNextTurn = async () => {
    if (!session || isNextTurnLoading || activeSummary || session.status === 'complete') return;
    const maxTurns = session.max_turns || 20;
    if ((session.turns || []).length >= maxTurns) {
      autoPlayRef.current = false;
      setAutoPlay(false);
      handleFetchSummary();
      return;
    }

    setIsNextTurnLoading(true);
    try {
      await nextTurn(session.debate_id);
      const updated = await getTranscript(session.debate_id);

      // Check if user clicked Pause while the request was in-flight
      if (!autoPlayRef.current) {
        setSession(updated);
        return;
      }

      setSession(updated);
      if ((updated.turns || []).length >= maxTurns || updated.status === 'complete') {
        autoPlayRef.current = false;
        setAutoPlay(false);
        handleFetchSummary(updated.debate_id);
      }
    } catch (err) {
      alert(`Failed to advance turn: ${err.message}`);
      autoPlayRef.current = false;
      setAutoPlay(false);
    } finally {
      setIsNextTurnLoading(false);
    }
  };

  const handleFetchSummary = async (debateId) => {
    autoPlayRef.current = false;
    setAutoPlay(false);
    const dId = debateId || session?.debate_id;
    if (!dId) return;
    try {
      const data = await getDebateSummary(dId);
      setActiveSummary(data);
      // Refresh transcript state so session.status === 'complete' is reflected in UI
      const updatedSess = await getTranscript(dId);
      setSession(updatedSess);
    } catch (err) {
      alert(`Failed to load summary: ${err.message}`);
    }
  };

  const handleReset = () => {
    autoPlayRef.current = false;
    setAutoPlay(false);
    setSession(null);
    setActiveSummary(null);
    setShowSetup(true);
  };

  if (showSetup) {
    return <TopicSetup onStartDebate={handleStartDebate} isLoading={isLoading} />;
  }

  const turns      = session?.turns || [];
  const maxTurns   = session?.max_turns || 20;
  const isComplete = turns.length >= maxTurns || session?.status === 'complete';
  const turnNum    = turns.length;

  const propModelName = session?.proposer_model || 'gemini-3.6-flash';
  const oppModelName  = session?.opponent_model || 'gemini-3.6-flash';

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <ArgumentGraph opacity={0.35} />

      {/* Sticky Header */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 40,
        backgroundColor: 'var(--bg-main)',
        borderBottom: '1px solid var(--border)',
        padding: '0 48px',
      }}>
        <div style={{
          maxWidth: 1180,
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          padding: '16px 0 12px',
          flexWrap: 'wrap',
          gap: 12,
        }}>
          <div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink-faint)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Turn {turnNum} of {maxTurns}{isComplete ? ' (complete)' : ''}
            </div>
            <div style={{ fontFamily: 'var(--serif)', fontWeight: 500, fontSize: 'clamp(18px, 2.5vw, 26px)', color: 'var(--ink-primary)', maxWidth: 640 }}>
              {session?.topic}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
            {/* Execution Group */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <button
                id="next-turn-btn"
                className="btn-action"
                onClick={handleNextTurn}
                disabled={isNextTurnLoading || isComplete}
                style={{ padding: '9px 24px', fontSize: 13.5, fontWeight: 600 }}
              >
                {isNextTurnLoading ? 'Reasoning…' : 'Next Turn →'}
              </button>

              <button
                id="autoplay-btn"
                className={`btn-outline ${autoPlay ? 'active' : ''}`}
                onClick={toggleAutoPlay}
                disabled={isComplete}
                style={{ padding: '9px 20px', fontSize: 13.5, minWidth: 110, justifyContent: 'center' }}
              >
                {autoPlay ? '⏸ Pause' : '▶ Auto-Run'}
              </button>

              <button
                id="autoscroll-btn"
                className={`btn-outline ${autoScroll ? 'active' : ''}`}
                onClick={() => setAutoScroll(prev => !prev)}
                title="Auto-scroll to keep latest response centered"
                style={{ padding: '9px 16px', fontSize: 13.5, display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <span>📜</span> {autoScroll ? 'Auto-Scroll: ON' : 'Auto-Scroll: OFF'}
              </button>
            </div>

            <div style={{ width: 1, height: 24, backgroundColor: 'var(--border)' }} />

            {/* Session Utilities Group */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <button
                id="verdict-btn"
                className="btn-outline"
                onClick={() => handleFetchSummary()}
                style={{ padding: '9px 20px', fontSize: 13.5 }}
              >
                🏆 Verdict
              </button>

              <button
                id="reset-btn"
                className="btn-outline"
                onClick={handleReset}
                title="Start a new debate"
                style={{ padding: '9px 18px', fontSize: 13.5, display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <span>↩</span> New Debate
              </button>
            </div>
          </div>
        </div>

        {/* Live session status */}
        <div style={{ maxWidth: 1180, margin: '0 auto', paddingBottom: 12, fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink-secondary)' }}>
          <span className="live-dot" />
          session live — {formatModelName(propModelName)} × {formatModelName(oppModelName)} · MCTS + propositional resolution
        </div>
      </header>

      {/* Spine & Timeline Content */}
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '72px 48px 88px', position: 'relative', zIndex: 10 }}>

        {turns.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '120px 0', color: 'var(--ink-faint)', fontFamily: 'var(--mono)', fontSize: 12 }}>
            Click "Next turn" to begin the debate.
          </div>
        ) : (
          <div style={{ position: 'relative' }}>
            {/* Center vertical spine line — constrained strictly to turns container */}
            <div style={{
              position: 'absolute',
              left: '50%',
              top: 24,
              bottom: 24,
              width: 1,
              backgroundColor: 'var(--border-strong)',
              transform: 'translateX(-50%)',
              zIndex: 0,
              transition: 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
            }} />

            {turns.map((turn, idx) => {
              const isAgentA  = turn.claim.speaker === 'agent_a';
              const isLatest  = (idx === turns.length - 1);
              const hasContra = turn.contradiction_result?.found;
              const hasMcts   = !!turn.mcts_trace;
              const cardModel = isAgentA ? propModelName : oppModelName;

              return (
                <React.Fragment key={idx}>
                  <ClaimEntry
                    turn={turn}
                    isAgentA={isAgentA}
                    isLatest={isLatest}
                    modelName={cardModel}
                    entryRef={isLatest ? lastTurnRef : null}
                    autoScroll={autoScroll}
                  />
                  {hasContra && <ContraEntry turn={turn} />}
                  {hasMcts   && <MctsEntry mctsTrace={turn.mcts_trace} turnNumber={turn.turn_number} />}
                </React.Fragment>
              );
            })}
          </div>
        )}
      </div>

      {/* Verdict Summary Modal */}
      {activeSummary && (
        <DebateSummaryModal summary={activeSummary} onClose={() => setActiveSummary(null)} />
      )}
    </div>
  );
}
