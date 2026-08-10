import React, { useState } from 'react';
import { Trophy, X, Target, Award, BookOpen, Sparkles, CheckCircle, ShieldAlert } from 'lucide-react';
import ThemeSwitcher from './ThemeSwitcher';

export default function DebateSummaryModal({ summary, onClose }) {
  const [activeTab, setActiveTab] = useState('coaching'); // 'coaching' | 'verdict' | 'transcript'
  const [coachingFilter, setCoachingFilter] = useState('all');
  const [transcriptFilter, setTranscriptFilter] = useState('all');

  if (!summary) return null;

  const isDraw   = summary.winner.includes('Draw');
  const isAgentA = summary.winner.includes('Agent A');

  const corneringPoints = summary.cornering_points || [];
  const proposerFull    = summary.proposer_full_arguments || summary.proposer_key_points || [];
  const opponentFull    = summary.opponent_full_arguments || summary.opponent_key_points || [];

  const filteredCornering = corneringPoints.filter(cp => {
    if (coachingFilter === 'agent_a') return cp.speaker.includes('Agent B');
    if (coachingFilter === 'agent_b') return cp.speaker.includes('Agent A');
    return true;
  });

  const allClaims = [
    ...proposerFull.map((text, idx) => ({ text, speaker: 'agent_a', speakerName: 'Agent A (Proposer)', index: idx + 1 })),
    ...opponentFull.map((text, idx) => ({ text, speaker: 'agent_b', speakerName: 'Agent B (Opponent)', index: idx + 1 }))
  ];

  const filteredClaims = allClaims.filter(c => {
    if (transcriptFilter === 'agent_a') return c.speaker === 'agent_a';
    if (transcriptFilter === 'agent_b') return c.speaker === 'agent_b';
    return true;
  });

  return (
    <div className="modal-overlay">
      <div className="modal-dialog">
        
        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', padding: '16px 24px', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ padding: 8, borderRadius: 5, backgroundColor: 'var(--agent-b-dim)', border: '1px solid var(--agent-b-border)' }}>
              <Trophy className="w-5 h-5" style={{ color: 'var(--agent-b)' }} />
            </div>
            <div>
              <h2 style={{ fontFamily: 'var(--serif)', fontWeight: 500, fontSize: 19, color: 'var(--ink-primary)', margin: 0 }}>
                Verdict Report
              </h2>
              <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink-faint)', marginTop: 2 }}>
                Topic: "{summary.topic}" · {summary.total_turns} turns completed
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <ThemeSwitcher />
            <button onClick={onClose} className="btn-icon" id="close-modal-x">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '12px 24px', borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-subtle)', flexShrink: 0 }}>
          <div style={{ display: 'flex', gap: 6 }}>
            <button
              onClick={() => setActiveTab('coaching')}
              className={`btn-outline ${activeTab === 'coaching' ? 'active' : ''}`}
              style={{ fontSize: 12, padding: '6px 14px' }}
            >
              <Target className="w-3.5 h-3.5" />
              <span>Tactical Coaching ({corneringPoints.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('verdict')}
              className={`btn-outline ${activeTab === 'verdict' ? 'active' : ''}`}
              style={{ fontSize: 12, padding: '6px 14px' }}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Logic Verdict</span>
            </button>

            <button
              onClick={() => setActiveTab('transcript')}
              className={`btn-outline ${activeTab === 'transcript' ? 'active' : ''}`}
              style={{ fontSize: 12, padding: '6px 14px' }}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Full Arguments ({proposerFull.length + opponentFull.length})</span>
            </button>
          </div>

          {/* Sub Filters */}
          {activeTab === 'coaching' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--ink-faint)' }}>Filter:</span>
              <button onClick={() => setCoachingFilter('all')} className={`btn-outline ${coachingFilter === 'all' ? 'active' : ''}`} style={{ padding: '3px 8px', fontSize: 11 }}>All</button>
              <button onClick={() => setCoachingFilter('agent_a')} className={`btn-outline ${coachingFilter === 'agent_a' ? 'active' : ''}`} style={{ padding: '3px 8px', fontSize: 11 }}>Agent A</button>
              <button onClick={() => setCoachingFilter('agent_b')} className={`btn-outline ${coachingFilter === 'agent_b' ? 'active' : ''}`} style={{ padding: '3px 8px', fontSize: 11 }}>Agent B</button>
            </div>
          )}

          {activeTab === 'transcript' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--ink-faint)' }}>Speaker:</span>
              <button onClick={() => setTranscriptFilter('all')} className={`btn-outline ${transcriptFilter === 'all' ? 'active' : ''}`} style={{ padding: '3px 8px', fontSize: 11 }}>All</button>
              <button onClick={() => setTranscriptFilter('agent_a')} className={`btn-outline ${transcriptFilter === 'agent_a' ? 'active' : ''}`} style={{ padding: '3px 8px', fontSize: 11 }}>Agent A</button>
              <button onClick={() => setTranscriptFilter('agent_b')} className={`btn-outline ${transcriptFilter === 'agent_b' ? 'active' : ''}`} style={{ padding: '3px 8px', fontSize: 11 }}>Agent B</button>
            </div>
          )}
        </div>

        {/* Tab Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* TAB 1: COACHING */}
          {activeTab === 'coaching' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              
              {/* Proposer Agent Strategic Debrief Header Card */}
              <div className="arena-card card-a" style={{ display: 'flex', flexDirection: 'column', gap: 12, backgroundColor: 'var(--agent-a-dim)', borderColor: 'var(--agent-a-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, borderBottom: '1px solid var(--agent-a-border)', paddingBottom: 8 }}>
                  <Sparkles className="w-4 h-4 text-agentA-primary" style={{ color: 'var(--agent-a)' }} />
                  <h4 style={{ fontFamily: 'var(--serif)', fontWeight: 600, fontSize: 15, color: 'var(--ink-primary)', margin: 0 }}>
                    Strategic Debrief by Agent A (Proposer)
                  </h4>
                </div>

                {summary.proposer_cornered_analysis && (
                  <div style={{ backgroundColor: 'var(--bg-main)', padding: 12, borderRadius: 6, border: '1px solid var(--border)' }}>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 11, fontWeight: 700, color: 'var(--contra)', display: 'block', marginBottom: 4 }}>
                      ⚠️ Proposer Vulnerability & Defense:
                    </span>
                    <p style={{ fontSize: 12.5, color: 'var(--ink-primary)', lineHeight: 1.5 }}>
                      {summary.proposer_cornered_analysis}
                    </p>
                  </div>
                )}

                {summary.opponent_cornered_analysis && (
                  <div style={{ backgroundColor: 'var(--bg-main)', padding: 12, borderRadius: 6, border: '1px solid var(--border)' }}>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 11, fontWeight: 700, color: 'var(--agent-a)', display: 'block', marginBottom: 4 }}>
                      🎯 Opponent Cornering Trap:
                    </span>
                    <p style={{ fontSize: 12.5, color: 'var(--ink-primary)', lineHeight: 1.5 }}>
                      {summary.opponent_cornered_analysis}
                    </p>
                  </div>
                )}

                {summary.opponent_escape_route && (
                  <div style={{ backgroundColor: 'var(--bg-main)', padding: 12, borderRadius: 6, border: '1px solid var(--border)' }}>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 11, fontWeight: 700, color: 'var(--agent-b)', display: 'block', marginBottom: 4 }}>
                      🚪 Opponent Escape Route (If Cornered):
                    </span>
                    <p style={{ fontSize: 12.5, color: 'var(--ink-primary)', lineHeight: 1.5 }}>
                      {summary.opponent_escape_route}
                    </p>
                  </div>
                )}
              </div>

              {filteredCornering.map((cp, idx) => {
                const isSpokenByB = cp.speaker.includes('Agent B');
                const defenderName = isSpokenByB ? 'Agent A (Proposer)' : 'Agent B (Opponent)';
                return (
                  <div key={idx} className="arena-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
                      <span className="badge-status contra">{cp.risk_level} Risk</span>
                      <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink-faint)' }}>
                        Attacker: <strong style={{ color: 'var(--ink-primary)' }}>{cp.speaker}</strong>
                      </span>
                    </div>

                    <div style={{ backgroundColor: 'var(--bg-subtle)', padding: 12, borderRadius: 4, border: '1px solid var(--border)' }}>
                      <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--ink-faint)', display: 'block', marginBottom: 4 }}>High-Risk Attack:</span>
                      <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink-primary)' }}>"{cp.point}"</p>
                      <p style={{ fontSize: 12, color: 'var(--ink-secondary)', marginTop: 6 }}>
                        <strong style={{ color: 'var(--contra)' }}>Vulnerability:</strong> {cp.why_dangerous}
                      </p>
                    </div>

                    <div style={{ backgroundColor: isSpokenByB ? 'var(--agent-a-dim)' : 'var(--agent-b-dim)', padding: 12, borderRadius: 4, border: `1px solid ${isSpokenByB ? 'var(--agent-a-border)' : 'var(--agent-b-border)'}` }}>
                      <span style={{ fontFamily: 'var(--mono)', fontSize: 10.5, fontWeight: 600, color: isSpokenByB ? 'var(--agent-a)' : 'var(--agent-b)', display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
                        <Sparkles className="w-3.5 h-3.5" /> Best Counter-Reply for {defenderName}:
                      </span>
                      <p style={{ fontSize: 13, color: 'var(--ink-primary)', lineHeight: 1.5 }}>{cp.best_reply}</p>

                      {cp.escape_route && (
                        <p style={{ fontSize: 11.5, color: 'var(--ink-secondary)', marginTop: 8, paddingTop: 6, borderTop: '1px dashed var(--border)' }}>
                          <strong style={{ color: 'var(--ink-primary)' }}>Escape Tactical Maneuver:</strong> {cp.escape_route}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* TAB 2: VERDICT */}
          {activeTab === 'verdict' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="arena-card" style={{ display: 'flex', alignItems: 'center', gap: 18, borderColor: isAgentA ? 'var(--agent-a-border)' : isDraw ? 'var(--border-strong)' : 'var(--agent-b-border)', backgroundColor: isAgentA ? 'var(--agent-a-dim)' : isDraw ? 'var(--bg-surface)' : 'var(--agent-b-dim)' }}>
                <Award className="w-10 h-10 shrink-0" style={{ color: isAgentA ? 'var(--agent-a)' : isDraw ? 'var(--ink-secondary)' : 'var(--agent-b)' }} />
                <div style={{ flex: 1 }}>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--ink-faint)', textTransform: 'uppercase' }}>Resolution Theorem Verdict</span>
                  <h3 style={{ fontSize: 20, fontWeight: 700, color: 'var(--ink-primary)', margin: '2px 0' }}>Winner: {summary.winner}</h3>
                  <p style={{ fontSize: 13, color: 'var(--ink-secondary)', lineHeight: 1.55 }}>{summary.winner_reasoning}</p>
                </div>
                <div style={{ backgroundColor: 'var(--bg-main)', padding: '10px 16px', borderRadius: 5, border: '1px solid var(--border)', textAlign: 'center' }}>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--ink-faint)', display: 'block' }}>Contradictions</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 16, fontWeight: 700, color: 'var(--contra)' }}>{summary.total_contradictions}</span>
                </div>
              </div>

              <div className="arena-card">
                <div style={{ fontFamily: 'var(--mono)', fontSize: 11, fontWeight: 600, color: 'var(--ink-primary)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Sparkles className="w-4 h-4" style={{ color: 'var(--agent-a)' }} /> Executive Logic Synthesis
                </div>
                <p style={{ fontSize: 13, color: 'var(--ink-secondary)', lineHeight: 1.65 }}>{summary.verdict_statement}</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
                <div className="arena-card card-a">
                  <h4 className="badge-agent-a" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                    <CheckCircle className="w-4 h-4" /> Agent A Key Arguments
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {(summary.proposer_key_points || []).map((pt, idx) => (
                      <div key={idx} style={{ fontSize: 12.5, color: 'var(--ink-primary)', backgroundColor: 'var(--bg-subtle)', padding: 10, borderRadius: 4, border: '1px solid var(--border)' }}>
                        {pt}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="arena-card card-b">
                  <h4 className="badge-agent-b" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                    <ShieldAlert className="w-4 h-4" /> Agent B Key Arguments
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {(summary.opponent_key_points || []).map((pt, idx) => (
                      <div key={idx} style={{ fontSize: 12.5, color: 'var(--ink-primary)', backgroundColor: 'var(--bg-subtle)', padding: 10, borderRadius: 4, border: '1px solid var(--border)' }}>
                        {pt}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: TRANSCRIPT */}
          {activeTab === 'transcript' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink-faint)' }}>
                <span>Displaying {filteredClaims.length} Claims</span>
                <span>Full Debate Log</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12 }}>
                {filteredClaims.map((claim, idx) => {
                  const isA = claim.speaker === 'agent_a';
                  return (
                    <div key={idx} className={isA ? 'arena-card card-a' : 'arena-card card-b'}>
                      <span className={isA ? 'badge-agent-a' : 'badge-agent-b'} style={{ fontSize: 10, display: 'block', marginBottom: 6 }}>
                        {claim.speakerName} · #{claim.index}
                      </span>
                      <p style={{ fontSize: 13, color: 'var(--ink-primary)', lineHeight: 1.5 }}>"{claim.text}"</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border)', padding: '14px 24px', backgroundColor: 'var(--bg-subtle)', flexShrink: 0 }}>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--ink-faint)' }}>
            Logic Propositional Engine · MCTS Selection
          </span>
          <button onClick={onClose} className="btn-action" id="close-modal-btn" style={{ padding: '8px 18px', fontSize: 12 }}>
            Close Report
          </button>
        </div>

      </div>
    </div>
  );
}
