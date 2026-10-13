import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { ScrollText, CheckCircle2, Loader2, Database, Bot, Cpu, Sparkles } from 'lucide-react';

const DOCKET_STEPS = [
  {
    id: 'docket',
    icon: ScrollText,
    title: 'Registering Case Docket',
    desc: 'Opening formal debate record and assigning docket session credentials...',
  },
  {
    id: 'facts',
    icon: Database,
    title: 'Grounded Fact Base Retrieval',
    desc: 'Querying 20 verifiable assertions and propositional clauses via Groq LPU...',
  },
  {
    id: 'semantic',
    icon: Sparkles,
    title: 'Building Propositional Index',
    desc: 'Compiling semantic retrieval vectors and resolution contradiction proofs...',
  },
  {
    id: 'agents',
    icon: Bot,
    title: 'Partitioning Agent Knowledge Bases',
    desc: 'Distributing grounded clauses between Proposer and Opponent memory spaces...',
  },
  {
    id: 'mcts',
    icon: Cpu,
    title: 'Priming MCTS Rebuttal Engine',
    desc: 'Calibrating Monte Carlo search simulation tree and tactical scoring heuristics...',
  },
];

export default function DebateInitializingOverlay({
  topic = 'Debate Resolution',
  maxTurns = 20,
  proposerModel = 'openai/gpt-oss-120b',
  opponentModel = 'deepseek/deepseek-r1-distill-llama-70b',
}) {
  const [currentStepIdx, setCurrentStepIdx] = useState(0);

  // Cycle through initialization milestones to match backend execution
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIdx(prev => {
        if (prev < DOCKET_STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 900);

    return () => clearInterval(interval);
  }, []);

  const formatModelName = (name) => {
    if (!name) return 'AI Agent';
    if (name.includes('/')) return name.split('/')[1];
    return name;
  };

  return createPortal(
    <div
      className="modal-overlay"
      style={{
        zIndex: 99999,
        padding: '24px',
        overflowY: 'auto',
      }}
    >
      {/* Background ambient radial glow */}
      <div
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 550,
          height: 550,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(251, 191, 36, 0.12) 0%, rgba(56, 189, 248, 0.08) 50%, transparent 70%)',
          pointerEvents: 'none',
          filter: 'blur(50px)',
          zIndex: 0,
        }}
      />

      {/* Main glassmorphic container */}
      <div
        className="modal-dialog"
        style={{
          maxWidth: 640,
          height: 'auto',
          maxHeight: '92vh',
          backgroundColor: 'var(--bg-surface, #14181f)',
          border: '1px solid var(--border-strong, #333d4d)',
          borderRadius: 16,
          boxShadow: '0 24px 60px -12px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05)',
          padding: '36px 32px 30px',
        }}
      >
        {/* Top Header Badge */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
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
              color: 'var(--gold, #fbbf24)',
            }}
          >
            <ScrollText className="w-3.5 h-3.5" />
            <span>Docket Initializing · Grounding Evidence</span>
          </div>
        </div>

        {/* Central Animated Pulsing Icon */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 22, position: 'relative' }}>
          <div
            style={{
              width: 76,
              height: 76,
              borderRadius: '50%',
              backgroundColor: 'var(--bg-elevated, #1a202a)',
              border: '2px solid var(--border-hi, #475569)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 35px rgba(251, 191, 36, 0.25)',
              position: 'relative',
            }}
          >
            {/* Spinning ring */}
            <div
              style={{
                position: 'absolute',
                inset: -6,
                borderRadius: '50%',
                border: '2px dashed var(--gold, #fbbf24)',
                opacity: 0.45,
                animation: 'spinSlow 12s linear infinite',
              }}
            />
            <Database
              className="w-8 h-8"
              style={{
                color: 'var(--gold, #fbbf24)',
                animation: 'pulseDocket 2.2s ease-in-out infinite',
              }}
            />
          </div>
        </div>

        {/* Title & Resolution Topic */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h2
            style={{
              fontFamily: 'var(--serif, serif)',
              fontWeight: 500,
              fontSize: 'clamp(22px, 3.5vw, 27px)',
              color: 'var(--ink-primary, #f8fafc)',
              margin: '0 0 8px',
              letterSpacing: '-0.01em',
            }}
          >
            Opening Debate Docket
          </h2>
          <p
            style={{
              fontFamily: 'var(--serif, Georgia)',
              fontStyle: 'italic',
              fontSize: 15,
              color: 'var(--ink-secondary, #94a3b8)',
              margin: 0,
              lineHeight: 1.45,
            }}
          >
            “{topic}”
          </p>
        </div>

        {/* Debater Cards Configuration Banner */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr',
            alignItems: 'center',
            gap: 12,
            backgroundColor: 'var(--bg-subtle, #11141a)',
            border: '1px solid var(--border, #232b36)',
            borderRadius: 10,
            padding: '10px 16px',
            marginBottom: 24,
          }}
        >
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--agent-a, #38bdf8)', textTransform: 'uppercase', marginBottom: 2 }}>
              Agent A (Proposer)
            </div>
            <div style={{ fontFamily: 'var(--sans, sans-serif)', fontSize: 12.5, fontWeight: 500, color: 'var(--ink-primary, #f8fafc)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {formatModelName(proposerModel)}
            </div>
          </div>

          <div style={{ textAlign: 'center', padding: '0 4px' }}>
            <span
              style={{
                fontFamily: 'var(--mono, monospace)',
                fontSize: 10,
                color: 'var(--ink-faint, #64748b)',
                textTransform: 'uppercase',
                border: '1px solid var(--border, #232b36)',
                borderRadius: 4,
                padding: '2px 6px',
              }}
            >
              {maxTurns} Turns
            </span>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: 10, color: 'var(--agent-b, #fbbf24)', textTransform: 'uppercase', marginBottom: 2 }}>
              Agent B (Opponent)
            </div>
            <div style={{ fontFamily: 'var(--sans, sans-serif)', fontSize: 12.5, fontWeight: 500, color: 'var(--ink-primary, #f8fafc)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {formatModelName(opponentModel)}
            </div>
          </div>
        </div>

        {/* Live Step Progression Checklist */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
          {DOCKET_STEPS.map((step, idx) => {
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
                    <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--gold, #fbbf24)' }} />
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
                          backgroundColor: 'var(--agent-b-dim, rgba(251, 191, 36, 0.15))',
                          color: 'var(--gold, #fbbf24)',
                          textTransform: 'uppercase',
                        }}
                      >
                        Loading…
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
              width: `${Math.min(100, Math.max(18, ((currentStepIdx + 1) / DOCKET_STEPS.length) * 100))}%`,
              background: 'linear-gradient(90deg, var(--gold, #fbbf24), var(--agent-a, #38bdf8))',
              borderRadius: 2,
              transition: 'width 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
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
          Extracting grounded logic facts and readying agents… Entering arena shortly.
        </div>
      </div>

      <style>{`
        @keyframes pulseDocket {
          0%, 100% { transform: scale(1); opacity: 0.9; }
          50%      { transform: scale(1.08); opacity: 1; filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.5)); }
        }
      `}</style>
    </div>,
    document.body
  );
}
