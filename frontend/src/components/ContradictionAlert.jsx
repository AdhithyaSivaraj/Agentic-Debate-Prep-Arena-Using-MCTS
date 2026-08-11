import React from 'react';
import { ShieldAlert, X, GitBranch } from 'lucide-react';

export default function ContradictionAlert({ contradictionResult, onClose }) {
  if (!contradictionResult || !contradictionResult.found) return null;

  const conflictingPairs = contradictionResult.conflicting_clauses || [];
  const proofSteps = contradictionResult.proof_steps || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-backdrop"
      style={{ background: 'rgba(0,0,0,0.78)', backdropFilter: 'blur(6px)' }}>

      <div className="relative w-full max-w-xl animate-modal glow-contradiction bg-arena-surface border border-alert-red/40 rounded-2xl shadow-2xl">

        
        <div className="h-1 w-full bg-gradient-to-r from-alert-red via-alert-orange to-alert-red/50 rounded-t-2xl" />

        <div className="p-6">
          
          <div className="flex items-start justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-alert-red/15 text-alert-red border border-alert-red/35">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Logical Contradiction Detected</h3>
                <p className="text-[11px] text-arena-muted mt-0.5 font-mono">
                  Propositional Resolution Refutation · Derived ⊥
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

          
          {conflictingPairs.length > 0 && (
            <div className="mb-5">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-alert-orange mb-2">
                Conflicting Clause Pair
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {conflictingPairs.map((pair, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-arena-bg border border-alert-red/25 space-y-2"
                  >
                    <div className="text-center">
                      <span className="block text-[9px] font-mono text-arena-muted uppercase mb-1">Clause A</span>
                      <code className="text-sm font-mono text-alert-red font-bold">{pair[0] || 'C₁'}</code>
                    </div>
                    <div className="flex items-center justify-center text-[10px] text-arena-muted gap-1">
                      <span className="h-px flex-1 bg-arena-border" />
                      ⚡ conflicts
                      <span className="h-px flex-1 bg-arena-border" />
                    </div>
                    <div className="text-center">
                      <span className="block text-[9px] font-mono text-arena-muted uppercase mb-1">Clause B</span>
                      <code className="text-sm font-mono text-alert-red font-bold">{pair[1] || 'C₂'}</code>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          
          {proofSteps.length > 0 && (
            <div className="mb-5">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-arena-muted mb-2 flex items-center gap-1.5">
                <GitBranch className="w-3 h-3" />
                Resolution Derivation Trace
              </p>
              <div className="max-h-36 overflow-y-auto p-3 rounded-xl bg-arena-bg border border-arena-border font-mono text-[11px] space-y-1">
                {proofSteps.map((step, idx) => (
                  <div
                    key={idx}
                    className={`px-2 py-1 rounded ${
                      step.includes('⊥')
                        ? 'bg-alert-red/20 text-alert-red font-bold border border-alert-red/35'
                        : 'text-arena-text'
                    }`}
                  >
                    {step}
                  </div>
                ))}
              </div>
            </div>
          )}

          
          <div className="p-3.5 rounded-xl bg-alert-red/8 border border-alert-red/20 text-[11px] text-arena-text leading-relaxed mb-5">
            <span className="font-semibold text-alert-red">Explainability Guarantee: </span>
            This contradiction was not guessed by an LLM. The propositional resolution algorithm
            derived the empty clause (⊥) from the agent's accumulated knowledge base — a formal proof.
          </div>

          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-5 py-2 text-xs font-semibold rounded-xl bg-arena-card hover:bg-arena-border text-white transition-colors border border-arena-border"
            >
              Close Proof Trace
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
