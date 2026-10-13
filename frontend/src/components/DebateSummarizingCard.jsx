import React, { useState, useEffect } from 'react';
import { Scale, CheckCircle2, Loader2, Sparkles, BrainCircuit, ShieldCheck, Award, Trophy, ArrowRight } from 'lucide-react';

const ANALYSIS_STEPS = [
  {
    id: 'audit',
    icon: BrainCircuit,
    title: 'Audit Debate Transcript',
    desc: 'Compiling all spoken arguments, propositional clauses, and grounded evidence...',
  },
  {
    id: 'resolution',
    icon: ShieldCheck,
    title: 'Verify Resolution Proofs',
    desc: 'Evaluating contradiction detection engine and cross-examining opposing premises...',
  },
  {
    id: 'mcts',
    icon: Scale,
    title: 'MCTS Strategy Traverse',
    desc: 'Comparing tactical move selections against rejected candidate rebuttals...',
  },
  {
    id: 'cornering',
    icon: Sparkles,
    title: 'Tactical Cornering & Escape Routes',
    desc: 'Determining exact high-threat verbal attacks, defenses, and strategic pivots...',
  },
  {
    id: 'verdict',
    icon: Award,
    title: 'Synthesize Official Verdict',
    desc: 'Formulating executive reasoning and determining final debater margin...',
  },
];

export default function DebateSummarizingCard({
  isSummarizing = false,
  summary = null,
  topic = 'Debate Topic',
  turnsCount = 0,
  maxTurns = 6,
  proposerModel = 'Agent A',
  opponentModel = 'Agent B',
  onViewFullReport,
}) {
  const [currentStepIdx, setCurrentStepIdx] = useState(0);

  // Smoothly advance through analytical milestones while summarizing
  useEffect(() => {
    if (!isSummarizing) return;
    const interval = setInterval(() => {
      setCurrentStepIdx(prev => {
        if (prev < ANALYSIS_STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 2400);

    return () => clearInterval(interval);
  }, [isSummarizing]);

  const formatModelName = (name) => {
    if (!name) return 'LLM';
    if (name.includes('/')) return name.split('/')[1];
    return name;
  };

  const agentATurns = Math.ceil(turnsCount / 2);
  const agentBTurns = Math.floor(turnsCount / 2);

  return (
    <div
      style={{
        position: 'relative',
        maxWidth: 720,
        margin: '48px auto 32px',
        zIndex: 20,
        animation: 'dialogScaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      }}
    >
      {/* Top Timeline Connector Node */}
      <div
        style={{
          position: 'absolute',
          top: -24,
          left: '50%',
          transform: 'translateX(-50%)',
          width: 14,
          height: 14,
          borderRadius: '50%',
          backgroundColor: isSummarizing ? 'var(--agent-b, #fbbf24)' : 'var(--valid, #34d399)',
          border: '3px solid var(--bg-main, #0d0f12)',
          boxShadow: isSummarizing
            ? '0 0 12px rgba(251, 191, 36, 0.6)'
            : '0 0 12px rgba(52, 211, 153, 0.6)',
          zIndex: 2,
        }}
      />

      {/* Main in-flow glassmorphic container */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface, #14181f)',
          border: '1px solid var(--border-strong, #333d4d)',
          borderRadius: 16,
          boxShadow: '0 20px 50px -10px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05)',
          overflow: 'hidden',
          padding: '32px 30px',
        }}
      >
        {isSummarizing ? (
          /* ============================================================
             1. LIVE SUMMARIZING STATE (Inline, never obscuring Turn 6!)
             ============================================================ */
          <div>
            {/* Header Badge */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 18 }}>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 14px',
                  borderRadius: 20,
                  backgroundColor: 'var(--bg-elevated, #1a202a)',
                  border: '1px solid var(--border, #232b36)',
                  fontFamily: 'var(--mono, monospace)',
                  fontSize: 11,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: 'var(--agent-b, #fbbf24)',
                }}
              >
                <Scale className="w-3.5 h-3.5" />
                <span>All {maxTurns} Turns Concluded · Summarizing Verdict</span>
              </div>
            </div>

            {/* Central Animated Pulsing Icon */}
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20, position: 'relative' }}>
              <div
                style={{
                  width: 68,
                  height: 68,
                  borderRadius: '50%',
                  backgroundColor: 'var(--bg-elevated, #1a202a)',
                  border: '2px solid var(--border-hi, #475569)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 25px rgba(56, 189, 248, 0.25)',
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    inset: -5,
                    borderRadius: '50%',
                    border: '2px dashed var(--agent-a, #38bdf8)',
                    opacity: 0.4,
                    animation: 'spinSlow 10s linear infinite',
                  }}
                />
                <Scale
                  className="w-7 h-7"
                  style={{
                    color: 'var(--agent-a, #38bdf8)',
                    animation: 'pulseScales 2.2s ease-in-out infinite',
                  }}
                />
              </div>
            </div>

            {/* Title & Topic */}
            <div style={{ textAlign: 'center', marginBottom: 22 }}>
              <h3
                style={{
                  fontFamily: 'var(--serif, serif)',
                  fontWeight: 500,
                  fontSize: 'clamp(20px, 3vw, 24px)',
                  color: 'var(--ink-primary, #f8fafc)',
                  margin: '0 0 6px',
                  letterSpacing: '-0.01em',
                }}
              >
                Summarizing Debate Arguments
              </h3>
              <p
                style={{
                  fontFamily: 'var(--serif, Georgia)',
                  fontStyle: 'italic',
                  fontSize: 14.5,
                  color: 'var(--ink-secondary, #94a3b8)',
                  margin: 0,
                  lineHeight: 1.4,
                }}
              >
                “{topic}”
              </p>
            </div>

            {/* Debater Cards Pill */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr auto 1fr',
                alignItems: 'center',
                gap: 12,
                backgroundColor: 'var(--bg-subtle, #11141a)',
                border: '1px solid var(--border, #232b36)',
                borderRadius: 10,
                padding: '9px 14px',
                marginBottom: 22,
              }}
            >
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--agent-a, #38bdf8)', textTransform: 'uppercase' }}>
                  Agent A (Proposer)
                </div>
                <div style={{ fontFamily: 'var(--sans, sans-serif)', fontSize: 12, fontWeight: 500, color: 'var(--ink-primary, #f8fafc)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {formatModelName(proposerModel)}
                </div>
                <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--ink-faint, #64748b)' }}>
                  {agentATurns} arguments
                </div>
              </div>

              <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 11, color: 'var(--ink-faint, #64748b)', padding: '0 6px' }}>
                ⚔️
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--agent-b, #fbbf24)', textTransform: 'uppercase' }}>
                  Agent B (Opponent)
                </div>
                <div style={{ fontFamily: 'var(--sans, sans-serif)', fontSize: 12, fontWeight: 500, color: 'var(--ink-primary, #f8fafc)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {formatModelName(opponentModel)}
                </div>
                <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--ink-faint, #64748b)' }}>
                  {agentBTurns} arguments
                </div>
              </div>
            </div>

            {/* Live Step Progression Checklist */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 22 }}>
              {ANALYSIS_STEPS.map((step, idx) => {
                const isCompleted = idx < currentStepIdx;
                const isCurrent = idx === currentStepIdx;
                const isPending = idx > currentStepIdx;

                return (
                  <div
                    key={step.id}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 12,
                      padding: '7px 10px',
                      borderRadius: 8,
                      backgroundColor: isCurrent ? 'var(--bg-elevated, #1a202a)' : 'transparent',
                      border: isCurrent ? '1px solid var(--border-strong, #333d4d)' : '1px solid transparent',
                      transition: 'all 0.25s ease',
                      opacity: isPending ? 0.35 : 1,
                    }}
                  >
                    <div style={{ marginTop: 2, flexShrink: 0 }}>
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--valid, #34d399)' }} />
                      ) : isCurrent ? (
                        <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--agent-a, #38bdf8)' }} />
                      ) : (
                        <div
                          style={{
                            width: 16,
                            height: 16,
                            borderRadius: '50%',
                            border: '1px dashed var(--ink-faint, #64748b)',
                          }}
                        />
                      )}
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontFamily: 'var(--sans, sans-serif)',
                          fontSize: 12.5,
                          fontWeight: isCurrent ? 600 : 500,
                          color: isCurrent
                            ? 'var(--ink-primary, #f8fafc)'
                            : isCompleted
                            ? 'var(--ink-secondary, #94a3b8)'
                            : 'var(--ink-faint, #64748b)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        <span>{step.title}</span>
                        {isCurrent && (
                          <span
                            style={{
                              fontSize: 9.5,
                              fontFamily: 'var(--mono, monospace)',
                              padding: '1px 6px',
                              borderRadius: 4,
                              backgroundColor: 'var(--agent-a-dim, rgba(56, 189, 248, 0.15))',
                              color: 'var(--agent-a, #38bdf8)',
                              textTransform: 'uppercase',
                            }}
                          >
                            In Progress
                          </span>
                        )}
                      </div>
                      {isCurrent && (
                        <div
                          style={{
                            fontFamily: 'var(--mono, monospace)',
                            fontSize: 11,
                            color: 'var(--ink-secondary, #94a3b8)',
                            marginTop: 2,
                            lineHeight: 1.35,
                          }}
                        >
                          {step.desc}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Shimmering Progress Bar */}
            <div
              style={{
                position: 'relative',
                height: 4,
                width: '100%',
                backgroundColor: 'var(--border, #232b36)',
                borderRadius: 2,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  bottom: 0,
                  width: `${Math.min(100, Math.max(15, ((currentStepIdx + 1) / ANALYSIS_STEPS.length) * 100))}%`,
                  background: 'linear-gradient(90deg, var(--agent-a, #38bdf8), var(--agent-b, #fbbf24))',
                  borderRadius: 2,
                  transition: 'width 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
                }}
              />
            </div>

            {/* Status ticker */}
            <div
              style={{
                textAlign: 'center',
                marginTop: 14,
                fontFamily: 'var(--mono, monospace)',
                fontSize: 11,
                color: 'var(--ink-faint, #64748b)',
              }}
            >
              All {maxTurns} turns concluded · compiling logic verdict & tactical debrief report…
            </div>
          </div>
        ) : summary ? (
          /* ============================================================
             2. VERDICT ANNOUNCEMENT STATE (Clickable to open full report)
             ============================================================ */
          <div style={{ textAlign: 'center' }}>
            {/* Top Badge */}
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '5px 14px', borderRadius: 20, backgroundColor: 'var(--valid-dim, rgba(52, 211, 153, 0.12))', border: '1px solid var(--valid-border, rgba(52, 211, 153, 0.35))', fontFamily: 'var(--mono, monospace)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--valid, #34d399)', marginBottom: 16 }}>
              <Trophy className="w-3.5 h-3.5" />
              <span>Debate Concluded · Official Verdict</span>
            </div>

            {/* Winner Heading */}
            <h3
              style={{
                fontFamily: 'var(--serif, serif)',
                fontWeight: 600,
                fontSize: 'clamp(24px, 4vw, 30px)',
                color: 'var(--ink-primary, #f8fafc)',
                margin: '0 0 10px',
                letterSpacing: '-0.015em',
              }}
            >
              {summary.winner}
            </h3>

            {/* Winner reasoning */}
            <p
              style={{
                fontFamily: 'var(--sans, sans-serif)',
                fontSize: 14,
                color: 'var(--ink-secondary, #94a3b8)',
                maxWidth: 580,
                margin: '0 auto 20px',
                lineHeight: 1.6,
              }}
            >
              {summary.winner_reasoning || summary.verdict_statement}
            </p>

            {/* Quick stats row */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                gap: 20,
                padding: '12px 0',
                borderTop: '1px dashed var(--border, #232b36)',
                borderBottom: '1px dashed var(--border, #232b36)',
                marginBottom: 24,
                fontFamily: 'var(--mono, monospace)',
                fontSize: 11.5,
                color: 'var(--ink-secondary, #94a3b8)',
              }}
            >
              <span>Turns: <strong style={{ color: 'var(--ink-primary)' }}>{summary.total_turns}</strong></span>
              <span>•</span>
              <span>Contradictions: <strong style={{ color: 'var(--contra, #f87171)' }}>{summary.total_contradictions}</strong></span>
              <span>•</span>
              <span>Tactical Points: <strong style={{ color: 'var(--gold, #fbbf24)' }}>{summary.cornering_points?.length || 0}</strong></span>
            </div>

            {/* Big Action Button to open Modal */}
            <button
              onClick={onViewFullReport}
              id="view-full-verdict-btn"
              className="btn-action"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '13px 28px',
                fontSize: 14,
                fontWeight: 600,
                margin: '0 auto',
              }}
            >
              <Trophy className="w-4 h-4" />
              <span>Open Detailed Verdict Report & Tactical Coaching</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
