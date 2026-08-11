import React, { useEffect, useRef } from 'react';
import { Sparkles, Brain, Database, ShieldCheck, ShieldAlert, Mic } from 'lucide-react';
import ClaimCard from './ClaimCard';

export default function AgentPanel({
  agentId,
  name,
  model,
  role,
  claims = [],
  kbCount = 0,
  hasContradiction = false,
  isActiveSpeaker = false,
  onInspectContradiction,
  onInspectMcts,
}) {
  const isAgentA = agentId === 'agent_a';
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [claims.length]);

  return (
    <div
      className={`flex flex-col h-full rounded-2xl border transition-all duration-400 ${
        isActiveSpeaker
          ? isAgentA
            ? 'bg-arena-surface border-agentA-primary/60 glow-agentA'
            : 'bg-arena-surface border-agentB-primary/60 glow-agentB'
          : isAgentA
          ? 'bg-arena-surface border-agentA-border/25'
          : 'bg-arena-surface border-agentB-border/25'
      }`}
    >
      
      <div className="flex items-center justify-between border-b border-arena-border/70 px-4 pt-4 pb-3.5 mb-1">
        <div className="flex items-center gap-3">
          
          <div
            className={`p-2 rounded-xl border transition-all ${
              isAgentA
                ? 'bg-agentA-badge text-agentA-primary border-agentA-border/40'
                : 'bg-agentB-badge text-agentB-primary border-agentB-border/40'
            }`}
          >
            {isAgentA ? <Sparkles className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-white text-sm">{name}</h3>
              <span className="text-[9px] uppercase tracking-widest px-2 py-0.5 rounded bg-arena-bg font-mono border border-arena-border/60 text-arena-muted">
                {role}
              </span>
            </div>
            <p className="text-[11px] font-mono text-arena-muted mt-0.5">{model}</p>
          </div>
        </div>

        
        <div className="flex flex-col items-end gap-1.5">
          
          {isActiveSpeaker && (
            <span
              className={`flex items-center gap-1.5 text-[10px] font-bold px-2.5 py-1 rounded-full border animate-subtle-pulse ${
                isAgentA
                  ? 'bg-agentA-badge text-agentA-primary border-agentA-border/50'
                  : 'bg-agentB-badge text-agentB-primary border-agentB-border/50'
              }`}
            >
              <Mic className="w-2.5 h-2.5" />
              Speaking
            </span>
          )}

          
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-arena-bg border border-arena-border/60 text-[11px]">
            <Database className="w-3 h-3 text-arena-muted" />
            <span className="font-mono text-white font-medium">{kbCount}</span>
            <span className="text-arena-muted">clauses</span>
          </div>

          
          <div className="flex items-center gap-1 text-[10px]">
            {hasContradiction ? (
              <span className="text-alert-red font-semibold flex items-center gap-1">
                <ShieldAlert className="w-2.5 h-2.5 animate-pulse" />
                Contradiction Flagged
              </span>
            ) : (
              <span className="text-proof-valid font-semibold flex items-center gap-1">
                <ShieldCheck className="w-2.5 h-2.5" />
                KB Consistent
              </span>
            )}
          </div>
        </div>
      </div>

      
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 pb-4 pt-2 space-y-2.5 min-h-[360px] max-h-[520px]"
      >
        {claims.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 border border-dashed border-arena-border/40 rounded-xl text-arena-muted text-xs mt-4">
            <div className={`w-8 h-8 rounded-full mb-3 flex items-center justify-center ${
              isAgentA ? 'bg-agentA-badge text-agentA-primary' : 'bg-agentB-badge text-agentB-primary'
            }`}>
              {isAgentA ? <Sparkles className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
            </div>
            <p className="font-medium">No claims yet</p>
            <p className="mt-1 text-[10px]">Advance the debate to begin reasoning.</p>
          </div>
        ) : (
          claims.map((turn, idx) => (
            <div key={idx} className="animate-slide-up">
              <ClaimCard
                claim={turn.claim}
                contradictionResult={turn.contradiction_result}
                mctsTrace={turn.mcts_trace}
                mode={turn.mode || 'live'}
                onInspectContradiction={onInspectContradiction}
                onInspectMcts={onInspectMcts}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
