import React, { useEffect, useRef } from 'react';
import { ScrollText, Sparkles, Brain, AlertTriangle, TreePine } from 'lucide-react';

export default function TranscriptLog({ turns = [], onInspectContradiction, onInspectMcts }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [turns.length]);

  return (
    <div className="flex flex-col h-full bg-arena-surface rounded-2xl border border-arena-border/70 overflow-hidden">
      
      <div className="flex items-center justify-between border-b border-arena-border/70 px-4 py-3.5 shrink-0">
        <div className="flex items-center gap-2">
          <ScrollText className="w-4 h-4 text-arena-muted" />
          <h3 className="font-bold text-white text-sm">Transcript</h3>
        </div>
        <span className="text-[10px] font-mono text-arena-muted bg-arena-bg px-2.5 py-1 rounded-md border border-arena-border/60">
          {turns.length} turns
        </span>
      </div>

      
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-3 py-3 space-y-1.5 min-h-[360px] max-h-[540px]"
      >
        {turns.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 border border-dashed border-arena-border/40 rounded-xl text-arena-muted text-xs">
            <p className="font-medium">Transcript empty</p>
            <p className="mt-1 text-[10px]">Click "Next Turn" to begin.</p>
          </div>
        ) : (
          turns.map((t, idx) => {
            const isAgentA = t.claim.speaker === 'agent_a';
            const hasContradiction = t.contradiction_result && t.contradiction_result.found;

            return (
              <div
                key={idx}
                className={`group relative px-3 py-2.5 rounded-xl border transition-all text-xs animate-slide-up overflow-hidden ${
                  isAgentA
                    ? 'bg-arena-bg border-agentA-border/20 hover:border-agentA-primary/40'
                    : 'bg-arena-bg border-agentB-border/20 hover:border-agentB-primary/40'
                } ${hasContradiction ? 'border-alert-red/40 bg-red-950/10' : ''}`}
              >
                
                <div className={`absolute left-0 top-0 bottom-0 w-[2.5px] rounded-l-xl ${
                  hasContradiction ? 'bg-alert-red' : isAgentA ? 'bg-agentA-primary' : 'bg-agentB-primary'
                }`} />

                <div className="pl-1">
                  
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wide flex items-center gap-0.5 ${
                        isAgentA
                          ? 'bg-agentA-badge text-agentA-primary'
                          : 'bg-agentB-badge text-agentB-primary'
                      }`}>
                        {isAgentA ? <Sparkles className="w-2 h-2" /> : <Brain className="w-2 h-2" />}
                        {isAgentA ? 'A' : 'B'}
                      </span>
                      <span className="font-mono text-[9px] text-arena-muted">#{t.turn_number}</span>
                    </div>

                    
                    <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      {hasContradiction && (
                        <button
                          onClick={() => onInspectContradiction && onInspectContradiction(t.contradiction_result)}
                          className="text-[9px] font-bold text-alert-red flex items-center gap-0.5 hover:underline px-1.5 py-0.5 rounded bg-alert-red/10 border border-alert-red/25"
                        >
                          <AlertTriangle className="w-2.5 h-2.5" />
                          Proof
                        </button>
                      )}
                      {t.mcts_trace && (
                        <button
                          onClick={() => onInspectMcts && onInspectMcts(t.mcts_trace, t.turn_number)}
                          className="text-[9px] text-agentA-primary flex items-center gap-0.5 hover:underline px-1.5 py-0.5 rounded bg-agentA-badge border border-agentA-border/30"
                        >
                          <TreePine className="w-2.5 h-2.5" />
                          MCTS
                        </button>
                      )}
                    </div>
                  </div>

                  
                  <p className="text-arena-text text-[11px] leading-relaxed mb-1.5 line-clamp-3">
                    {t.claim.text}
                  </p>

                  
                  <div className="font-mono text-[9px] text-arena-muted/70">
                    ∴ {t.claim.propositional_form}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
