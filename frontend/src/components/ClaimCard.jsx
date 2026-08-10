import React from 'react';
import { AlertTriangle, CheckCircle, Cpu, WifiOff, TreePine } from 'lucide-react';

export default function ClaimCard({ claim, contradictionResult, mctsTrace, mode = 'live', onInspectContradiction, onInspectMcts }) {
  const isAgentA = claim.speaker === 'agent_a';
  const isContradicted = claim.is_contradicted || (contradictionResult && contradictionResult.found);
  const isLive = mode === 'live';

  return (
    <div
      className={`relative rounded-xl border transition-all duration-300 overflow-hidden
        ${isAgentA
          ? 'bg-arena-card border-agentA-border/25 hover:border-agentA-primary/50'
          : 'bg-arena-card border-agentB-border/25 hover:border-agentB-primary/50'}
        ${isContradicted
          ? 'border-alert-red/60 bg-red-950/15 animate-contradiction'
          : ''}
      `}
    >
      {/* Left accent bar */}
      <div
        className={`absolute left-0 top-0 bottom-0 w-[3px] rounded-l-xl ${
          isContradicted
            ? 'bg-alert-red'
            : isAgentA
            ? 'bg-agentA-primary'
            : 'bg-agentB-primary'
        }`}
      />

      <div className="pl-4 pr-3 pt-3 pb-3">
        {/* Top row: agent badge + turn + mode + status */}
        <div className="flex items-center justify-between mb-2.5 gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 flex-wrap">
            {/* Agent badge */}
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide flex items-center gap-1 ${
              isAgentA
                ? 'bg-agentA-badge text-agentA-primary border border-agentA-border/40'
                : 'bg-agentB-badge text-agentB-primary border border-agentB-border/40'
            }`}>
              {isAgentA ? 'A' : 'B'} · Turn #{claim.turn_number}
            </span>

            {/* Live/offline badge */}
            <span className={`px-2 py-0.5 rounded-md text-[9px] font-mono flex items-center gap-1 border ${
              isLive
                ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/40'
                : 'bg-amber-950/30 text-amber-400/70 border-amber-800/30'
            }`}>
              {isLive ? <Cpu className="w-2 h-2" /> : <WifiOff className="w-2 h-2" />}
              {isLive ? 'Live API' : 'Offline'}
            </span>
          </div>

          {/* Contradiction / Verified badge */}
          {isContradicted ? (
            <button
              onClick={() => onInspectContradiction && onInspectContradiction(contradictionResult)}
              className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md bg-alert-red/15 text-alert-red border border-alert-red/40 hover:bg-alert-red/25 transition-colors"
            >
              <AlertTriangle className="w-2.5 h-2.5 animate-pulse" />
              ⚡ Contradiction
            </button>
          ) : (
            <span className="flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-md bg-proof-validBg text-proof-valid border border-proof-valid/25">
              <CheckCircle className="w-2.5 h-2.5" />
              Verified
            </span>
          )}
        </div>

        {/* Claim text */}
        <p className="text-sm text-arena-text leading-relaxed font-normal mb-3">
          {claim.text}
        </p>

        {/* Footer: clause + MCTS link */}
        <div className="flex items-center justify-between pt-2 border-t border-arena-border/40">
          <div className="flex items-center gap-1.5 font-mono text-[10px] bg-arena-bg/80 px-2 py-1 rounded-md border border-arena-border/50">
            <span className="text-arena-muted">∴</span>
            <span className={isAgentA ? 'text-agentA-primary' : 'text-agentB-primary'}>
              {claim.propositional_form || 'P'}
            </span>
          </div>

          {mctsTrace && (
            <button
              onClick={() => onInspectMcts && onInspectMcts(mctsTrace, claim.turn_number)}
              className="flex items-center gap-1 text-[10px] font-mono text-arena-muted hover:text-agentA-primary transition-colors"
            >
              <TreePine className="w-3 h-3" />
              MCTS ({mctsTrace.n_simulations || 10} sims)
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
