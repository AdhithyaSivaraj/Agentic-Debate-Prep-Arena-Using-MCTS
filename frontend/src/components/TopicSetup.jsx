import React, { useState, useEffect, useRef } from 'react';
import ArgumentGraph from './ArgumentGraph';
import ThemeSwitcher from './ThemeSwitcher';

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

const MODEL_GROUPS = [
  {
    name: 'Premier Open Models (Llama 3.3 70B & DeepSeek R1)',
    models: [
      { id: 'meta-llama/llama-3.3-70b-instruct', label: 'Meta Llama 3.3 70B Instruct' },
      { id: 'deepseek/deepseek-r1-distill-llama-70b', label: 'DeepSeek R1 Distill 70B (Logic Reasoning)' },
      { id: 'deepseek/deepseek-r1', label: 'DeepSeek R1 (Full Reasoning Engine)' },
    ],
  },
  {
    name: 'Groq LPU (Ultra-Fast ~300-1000 tokens/s)',
    models: [
      { id: 'openai/gpt-oss-120b', label: 'GPT-OSS 120B (Groq LPU — ~500 t/s)' },
      { id: 'openai/gpt-oss-20b', label: 'GPT-OSS 20B (Groq LPU — ~1000 t/s)' },
      { id: 'qwen/qwen3.6-27b', label: 'Qwen 3.6 27B (Groq LPU)' },
    ],
  },
  {
    name: 'Google Gemini (Gemini Key)',
    models: [
      { id: 'gemini-3.6-flash', label: 'Gemini 3.6 Flash' },
      { id: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash' },
      { id: 'gemini-3.1-flash-lite', label: 'Gemini 3.1 Flash Lite' },
    ],
  },
];

let docketCounter = Math.floor(Math.random() * 8900) + 100;

export default function TopicSetup({ onStartDebate, isLoading }) {
  const [topic, setTopic] = useState('');
  const [userInteracted, setUserInteracted] = useState(false);
  const [maxTurns, setMaxTurns] = useState(20);
  const [proposerModel, setProposerModel] = useState('meta-llama/llama-3.3-70b-instruct');
  const [opponentModel, setOpponentModel] = useState('deepseek/deepseek-r1-distill-llama-70b');
  const [deriveLines, setDeriveLines] = useState([]);
  const [titleVisible, setTitleVisible] = useState(false);

  const docketNo = useRef(String(docketCounter).padStart(4, '0'));

  
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
    <div style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden' }}>
      
      <ArgumentGraph opacity={0.65} />

      
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
              fontFamily: 'var(--serif)',
              fontWeight: 500,
              fontSize: 'clamp(44px, 8.5vw, 100px)',
              lineHeight: 0.96,
              letterSpacing: '-0.015em',
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
                    style={{
                      width: '100%',
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border)',
                      borderRadius: 4,
                      padding: '6px 8px',
                      fontFamily: 'var(--mono)',
                      fontSize: 11,
                      color: 'var(--ink-primary)',
                      outline: 'none',
                    }}
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
                    style={{
                      width: '100%',
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border)',
                      borderRadius: 4,
                      padding: '6px 8px',
                      fontFamily: 'var(--mono)',
                      fontSize: 11,
                      color: 'var(--ink-primary)',
                      outline: 'none',
                    }}
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

          
          <div
            className="anim-fade-up"
            style={{
              animationDelay: '1.08s',
              marginTop: 24,
              fontFamily: 'var(--mono)',
              fontSize: 10,
              color: 'var(--ink-faint)',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span style={{ width: 22, height: 1, backgroundColor: 'var(--ink-faint)', display: 'inline-block' }} />
            scroll to enter the arena
          </div>

        </div>
      </div>
    </div>
  );
}
