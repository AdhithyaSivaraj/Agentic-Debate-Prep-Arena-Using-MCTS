import React, { useState, useEffect } from 'react';
import ThemeSwitcher from './ThemeSwitcher';
import { MODEL_GROUPS, DEFAULT_PROPOSER, DEFAULT_OPPONENT } from '../lib/models';

const SUGGESTED = [
  { n: '01', text: 'Should AI development be globally regulated?' },
  { n: '02', text: 'Is UBI effective against automation?' },
  { n: '03', text: 'Should standardized exams be abolished?' },
  { n: '04', text: 'Should social media be a public utility?' },
];

const AUTO_TOPICS = [
  'Should standardized exams be abolished?',
  'Should AI development be globally regulated?',
  'Is UBI effective against automation?',
  'Should social media be a public utility?',
  'Will humanity attain AGI by 2030?',
];

const DERIVE_LINES = [
  'assert(premise_1 → conclusion)',
  'assert(¬conclusion ∨ ¬evidence)',
  'resolve(claim_1, claim_2) ⊢ ⊥',
];

export default function TopicSetup({ onStartDebate, isLoading }) {
  const [topic, setTopic] = useState('');
  const [userInteracted, setUserInteracted] = useState(false);
  const [maxTurns, setMaxTurns] = useState(20);
  const [proposerModel, setProposerModel] = useState(DEFAULT_PROPOSER);
  const [opponentModel, setOpponentModel] = useState(DEFAULT_OPPONENT);
  const [deriveLines, setDeriveLines] = useState([]);
  const [titleVisible, setTitleVisible] = useState(false);


  useEffect(() => {
    let idx = 0;
    const show = () => {
      if (idx >= DERIVE_LINES.length) {
        setTimeout(() => setTitleVisible(true), 100);
        return;
      }
      setDeriveLines(prev => [...prev, DERIVE_LINES[idx]]);
      idx++;
      setTimeout(show, 400);
    };
    const t = setTimeout(show, 250);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (userInteracted) return;

    let topicIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let timerId;

    const typeStep = () => {
      const currentTopic = AUTO_TOPICS[topicIndex % AUTO_TOPICS.length];

      if (isDeleting) {
        charIndex--;
        setTopic(currentTopic.substring(0, charIndex));

        if (charIndex === 0) {
          isDeleting = false;
          topicIndex++;
          timerId = setTimeout(typeStep, 350);
          return;
        }
        timerId = setTimeout(typeStep, 25);
      } else {
        charIndex++;
        setTopic(currentTopic.substring(0, charIndex));

        if (charIndex === currentTopic.length) {
          isDeleting = true;
          timerId = setTimeout(typeStep, 2200);
          return;
        }
        timerId = setTimeout(typeStep, 45);
      }
    };

    timerId = setTimeout(typeStep, 400);

    return () => clearTimeout(timerId);
  }, [userInteracted]);

  const handleInputChange = (e) => {
    setUserInteracted(true);
    setTopic(e.target.value);
  };

  const handleInputFocus = () => {
    if (!userInteracted) {
      setUserInteracted(true);
      setTopic('');
    }
  };

  const handleInputBlur = () => {
    if (!topic.trim()) {
      setUserInteracted(false);
    }
  };

  const handleChipClick = (chipText) => {
    setUserInteracted(true);
    setTopic(chipText);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim() && !isLoading) {
      onStartDebate(topic.trim(), maxTurns, proposerModel, opponentModel);
    }
  };

  return (
    <div className="anim-page-enter" style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden' }}>
      <div style={{ position: 'fixed', top: 20, right: 24, zIndex: 20 }}>
        <ThemeSwitcher />
      </div>
      <div style={{ position: 'relative', zIndex: 10 }}>
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '0 clamp(24px, 5vw, 64px)',
          maxWidth: '1160px',
          margin: '0 auto',
        }}>
          <div className="anim-fade-up" style={{ animationDelay: '0.08s', fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--ink-faint)', marginBottom: 20 }}>
            Logic-verified argument coaching engine
          </div>
          <div style={{ marginBottom: 12, minHeight: 64 }}>
            {deriveLines.map((line, i) => (
              <div key={i} className="derive-line show" style={{ animationDelay: `${i * 0.04}s` }}>
                {line}
              </div>
            ))}
          </div>
          <h1
            className={`anim-title ${titleVisible ? 'reveal' : ''}`}
            style={{
              fontFamily: 'var(--display)',
              fontStyle: 'var(--display-style)',
              fontWeight: 400,
              fontSize: 'clamp(48px, 9vw, 112px)',
              lineHeight: 0.95,
              letterSpacing: '-0.02em',
              margin: '0 0 24px',
              maxWidth: 900,
              color: 'var(--ink-primary)',
            }}
          >
            Agentic <em style={{ fontStyle: 'italic', color: 'var(--agent-b)' }}>Debate</em> Arena
          </h1>
          <p
            className="anim-fade-up"
            style={{
              animationDelay: '0.45s',
              fontSize: '16px',
              lineHeight: 1.7,
              color: 'var(--ink-secondary)',
              maxWidth: 480,
              margin: '0 0 36px',
            }}
          >
            Two autonomous debaters. A resolution engine that catches every contradiction.
            A search tree that picks each rebuttal on purpose — nothing said without reason.
          </p>
          <form onSubmit={handleSubmit}>
            <div
              className="anim-fade-up docket-container"
              style={{ animationDelay: '0.6s', maxWidth: 640, marginBottom: 16, position: 'relative' }}
            >
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--ink-faint)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
                Case topic
              </div>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                <input
                  type="text"
                  value={topic}
                  onChange={handleInputChange}
                  onFocus={handleInputFocus}
                  onBlur={handleInputBlur}
                  disabled={isLoading}
                  className="docket-input"
                  placeholder="Enter a debate resolution…"
                  id="debate-topic-input"
                  autoComplete="off"
                />
                {!userInteracted && (
                  <span
                    style={{
                      display: 'inline-block',
                      width: 2,
                      height: 22,
                      backgroundColor: 'var(--agent-a)',
                      marginLeft: 2,
                      animation: 'livePulse 0.8s ease-in-out infinite',
                    }}
                  />
                )}
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
                padding: '12px 0',
                borderTop: '1px dashed var(--border)',
                borderBottom: '1px dashed var(--border)',
                marginBottom: 12,
              }}>
                <div>
                  <label htmlFor="proposer-model-select" style={{ display: 'block', fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--agent-a)', marginBottom: 4, textTransform: 'uppercase' }}>
                    Agent A (Proposer)
                  </label>
                  <select
                    id="proposer-model-select"
                    value={proposerModel}
                    onChange={e => setProposerModel(e.target.value)}
                    disabled={isLoading}
                    className="docket-select"
                  >
                    {MODEL_GROUPS.map(group => (
                      <optgroup key={group.name} label={group.name}>
                        {group.models.map(m => (
                          <option key={m.id} value={m.id}>{m.label}</option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="opponent-model-select" style={{ display: 'block', fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--agent-b)', marginBottom: 4, textTransform: 'uppercase' }}>
                    Agent B (Opponent)
                  </label>
                  <select
                    id="opponent-model-select"
                    value={opponentModel}
                    onChange={e => setOpponentModel(e.target.value)}
                    disabled={isLoading}
                    className="docket-select"
                  >
                    {MODEL_GROUPS.map(group => (
                      <optgroup key={group.name} label={group.name}>
                        {group.models.map(m => (
                          <option key={m.id} value={m.id}>{m.label}</option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
              </div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink-faint)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Max Turns Limit
                </span>
                <select
                  value={maxTurns}
                  onChange={e => setMaxTurns(Number(e.target.value))}
                  disabled={isLoading}
                  style={{
                    border: 'none',
                    background: 'transparent',
                    fontFamily: 'var(--mono)',
                    fontSize: 12,
                    color: 'var(--ink-secondary)',
                    cursor: 'pointer',
                    outline: 'none',
                  }}
                  id="max-turns-select"
                >
                  <option value={6}>6 turns</option>
                  <option value={10}>10 turns</option>
                  <option value={20}>20 turns</option>
                  <option value={30}>30 turns</option>
                </select>
              </div>
            </div>
            <div
              className="anim-fade-up"
              style={{
                animationDelay: '0.72s',
                display: 'flex',
                flexWrap: 'wrap',
                gap: 8,
                marginBottom: 36,
                maxWidth: 640,
              }}
            >
              {SUGGESTED.map(item => (
                <div
                  key={item.n}
                  className="docket-chip"
                  onClick={() => handleChipClick(item.text)}
                  id={`suggest-${item.n}`}
                >
                  <span className="num">{item.n}</span>
                  {item.text}
                </div>
              ))}
            </div>
            <div className="anim-fade-up" style={{ animationDelay: '0.85s', display: 'flex', alignItems: 'center', gap: 14 }}>
              <button
                type="submit"
                id="open-docket-btn"
                className="btn-action"
                disabled={!topic.trim() || isLoading}
                style={{ padding: '14px 34px', fontSize: 14 }}
              >
                {isLoading ? 'Building knowledge base…' : 'Open the docket →'}
              </button>
              {isLoading && (
                <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink-faint)' }}>
                  Loading facts into resolution engine…
                </span>
              )}
            </div>
          </form>
          <div
            className="anim-fade-up"
            style={{
              animationDelay: '0.98s',
              marginTop: 48,
              fontFamily: 'var(--mono)',
              fontSize: 10.5,
              color: 'var(--ink-faint)',
            }}
          >
            Unit IV — propositional resolution · Unit III — Monte Carlo tree search · Unit II — semantic retrieval
          </div>
        </div>
      </div>
    </div>
  );
}
