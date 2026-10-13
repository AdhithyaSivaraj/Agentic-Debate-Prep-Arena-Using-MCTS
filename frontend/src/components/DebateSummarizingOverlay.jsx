import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Scale, CheckCircle2, Loader2, Sparkles, BrainCircuit, ShieldCheck, Award, MessageSquare } from 'lucide-react';

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

export default function DebateSummarizingOverlay({
  topic = 'Debate Topic',
  turnsCount = 0,
  maxTurns = 6,
  proposerModel = 'Agent A',
  opponentModel = 'Agent B',
  lastOpponentClaim = '',
}) {
  const [currentStepIdx, setCurrentStepIdx] = useState(0);

  // Smoothly advance through analytical milestones
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIdx(prev => {
        if (prev < ANALYSIS_STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 2400);

    return () => clearInterval(interval);
  }, []);

  const formatModelName = (name) => {
    if (!name) return 'LLM';
    if (name.includes('/')) return name.split('/')[1];
    return name;
  };

  const agentATurns = Math.ceil(turnsCount / 2);
  const agentBTurns = Math.floor(turnsCount / 2);

  return createPortal(
    <div
      className="modal-overlay"
      style={{
        zIndex: 99999,
        padding: '24px',
        overflowY: 'auto',
      }}
    >
      {/* Background ambient glowing gradient */}
      <div
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 550,
          height: 550,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(56, 189, 248, 0.16) 0%, rgba(251, 191, 36, 0.12) 45%, transparent 70%)',
          pointerEvents: 'none',
          filter: 'blur(45px)',
          zIndex: 0,
        }}
      />

      {/* Main glassmorphic container */}
      <div
        className="modal-dialog"
        style={{
          position: 'relative',
          maxWidth: 640,
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          backgroundColor: 'var(--bg-surface, #14181f)',
          border: '1px solid var(--border-strong, #333d4d)',
          borderRadius: 16,
          boxShadow: '0 24px 60px -12px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.06)',
          padding: '28px 24px 24px',
          zIndex: 1,
        }}
      >
        {/* Top Header Badge */}
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
            <span>Debate Concluded · Synthesizing Verdict</span>
          </div>
        </div>

        {/* Central Animated Pulsing Icon */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20, position: 'relative' }}>
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: '50%',
              backgroundColor: 'var(--bg-elevated, #1a202a)',
              border: '2px solid var(--border-hi, #475569)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 30px rgba(56, 189, 248, 0.3)',
              position: 'relative',
            }}
          >
            {/* Spinning decorative ring */}
            <div
              style={{
                position: 'absolute',
                inset: -6,
                borderRadius: '50%',
                border: '2px dashed var(--agent-a, #38bdf8)',
                opacity: 0.45,
                animation: 'spinSlow 10s linear infinite',
              }}
            />
            <Scale
              className="w-8 h-8"
              style={{
                color: 'var(--agent-a, #38bdf8)',
                animation: 'pulseScales 2.2s ease-in-out infinite',
              }}
            />
          </div>
        </div>

        {/* Title & Topic */}
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <h2
            style={{
              fontFamily: 'var(--serif, serif)',
              fontWeight: 500,
              fontSize: 'clamp(22px, 3.5vw, 26px)',
              color: 'var(--ink-primary, #f8fafc)',
              margin: '0 0 6px',
              letterSpacing: '-0.01em',
            }}
          >
            Summarizing Debate Arguments
          </h2>
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

        {/* Opposer's Closing Claim Quote (Ensures Opposer's point is always prominent and readable!) */}
        {lastOpponentClaim && (
          <div
            style={{
              backgroundColor: 'var(--bg-subtle, #11141a)',
              border: '1px solid var(--agent-b-border, rgba(251, 191, 36, 0.35))',
              borderRadius: 8,
              padding: '10px 14px',
              marginBottom: 20,
              textAlign: 'left',
            }}
          >
            <div
              style={{
                fontFamily: 'var(--mono, monospace)',
                fontSize: 10.5,
                color: 'var(--agent-b, #fbbf24)',
                textTransform: 'uppercase',
                marginBottom: 4,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Opposer's Closing Argument (Turn {turnsCount})</span>
            </div>
            <div
              style={{
                fontFamily: 'var(--serif, Georgia)',
                fontStyle: 'italic',
                fontSize: 13.5,
                color: 'var(--ink-primary, #f8fafc)',
                lineHeight: 1.45,
              }}
            >
              “{lastOpponentClaim}”
            </div>
          </div>
        )}

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
            <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--agent-a, #38bdf8)', textTransform: 'uppercase', marginBottom: 2 }}>
              Agent A (Proposer)
            </div>
            <div style={{ fontFamily: 'var(--sans, sans-serif)', fontSize: 12, fontWeight: 500, color: 'var(--ink-primary, #f8fafc)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {formatModelName(proposerModel)}
            </div>
            <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--ink-faint, #64748b)', marginTop: 2 }}>
              {agentATurns} {agentATurns === 1 ? 'argument' : 'arguments'}
            </div>
          </div>

          <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 11, color: 'var(--ink-faint, #64748b)', padding: '0 8px' }}>
            ⚔️
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--agent-b, #fbbf24)', textTransform: 'uppercase', marginBottom: 2 }}>
              Agent B (Opponent)
            </div>
            <div style={{ fontFamily: 'var(--sans, sans-serif)', fontSize: 12, fontWeight: 500, color: 'var(--ink-primary, #f8fafc)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {formatModelName(opponentModel)}
            </div>
            <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--ink-faint, #64748b)', marginTop: 2 }}>
              {agentBTurns} {agentBTurns === 1 ? 'argument' : 'arguments'}
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
              transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          />
        </div>

        {/* Bottom micro-copy */}
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

      <style>{`
        @keyframes spinSlow {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes pulseScales {
          0%, 100% { transform: scale(1); opacity: 0.9; }
          50%      { transform: scale(1.08); opacity: 1; filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.5)); }
        }
      `}</style>
    </div>,
    document.body
  );
}
