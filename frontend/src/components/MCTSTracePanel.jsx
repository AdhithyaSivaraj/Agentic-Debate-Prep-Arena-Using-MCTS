import React from 'react';
import { TreePine, X, Check, Info } from 'lucide-react';

export default function MCTSTracePanel({ mctsTrace, turnNumber, onClose }) {
  if (!mctsTrace) return null;

  const chosenRebuttal = mctsTrace.chosen_rebuttal;
  const rejectedCandidates = mctsTrace.rejected_candidates || [];
  const nSimulations = mctsTrace.n_simulations || 10;

  
  const allScores = rejectedCandidates.map(c => Math.abs(c.score));
  const maxScore = Math.max(...allScores, 0.01);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-backdrop"
      style={{ background: 'rgba(0,0,0,0.78)', backdropFilter: 'blur(6px)' }}
    >
      <div className="relative w-full max-w-2xl animate-modal bg-arena-surface border border-agentA-border/40 rounded-2xl shadow-2xl">

        
        <div className="h-1 w-full bg-gradient-to-r from-agentA-primary/80 via-agentA-primary to-agentA-primary/30 rounded-t-2xl" />

        <div className="p-6">
          
          <div className="flex items-start justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-agentA-badge text-agentA-primary border border-agentA-border/40">
                <TreePine className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  MCTS Rebuttal Trace {turnNumber ? `· Turn #${turnNumber}` : ''}
                </h3>
                <p className="text-[11px] text-arena-muted mt-0.5 font-mono">
                  {nSimulations} simulations · UCB1 selection · heuristic scoring
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-arena-muted hover:text-white hover:bg-arena-card transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          
          <div className="mb-5">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-agentA-primary mb-2 flex items-center gap-1">
              <Check className="w-3 h-3" /> Selected by MCTS
            </p>
            <div className="p-4 rounded-xl glow-winner bg-agentA-badge/20 border-2 border-agentA-primary/60">
              <p className="text-sm font-medium text-white leading-relaxed mb-2.5">
                "{chosenRebuttal}"
              </p>
              <div className="flex items-center gap-3 text-[10px] font-mono text-agentA-primary">
                <span className="px-2 py-0.5 rounded bg-agentA-badge border border-agentA-border/40">Winner</span>
                <span>Highest Visit Count</span>
              </div>
            </div>
          </div>

          
          {rejectedCandidates.length > 0 && (
            <div className="mb-5">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-arena-muted mb-2 flex items-center gap-1">
                <X className="w-3 h-3" /> Evaluated & Rejected
              </p>
              <div className="space-y-2 stagger-child">
                {rejectedCandidates.map((cand, idx) => {
                  const pct = maxScore > 0 ? Math.min(100, (Math.abs(cand.score) / maxScore) * 85) : 5;
                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-arena-bg border border-arena-border/50 opacity-60 hover:opacity-90 transition-opacity"
                    >
                      <p className="text-[11px] text-arena-text mb-2 leading-relaxed line-clamp-2">
                        "{cand.text}"
                      </p>
                      
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1 bg-arena-border/60 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-arena-muted/50 rounded-full animate-score-fill"
                            style={{ '--score-width': `${pct}%` }}
                          />
                        </div>
                        <span className="font-mono text-[9px] text-arena-muted whitespace-nowrap">
                          {cand.score} · {cand.visit_count}v
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          
          <div className="p-3 rounded-xl bg-arena-bg border border-arena-border/60 text-[11px] text-arena-muted flex items-start gap-2 mb-5">
            <Info className="w-3.5 h-3.5 text-agentA-primary shrink-0 mt-0.5" />
            <span>
              <strong className="text-white">Explainable AI:</strong> The LLM provided candidate phrasings.
              MCTS selected the winner by scoring simulated outcomes via{' '}
              <code className="font-mono text-agentA-primary">contradictions_forced − received + 0.1·claim_spread</code>.
            </span>
          </div>

          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-5 py-2 text-xs font-semibold rounded-xl bg-arena-card hover:bg-arena-border text-white transition-colors border border-arena-border"
            >
              Close Trace
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
