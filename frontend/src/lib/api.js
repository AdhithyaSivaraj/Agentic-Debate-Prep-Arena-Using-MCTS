

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJSON(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}`;
    try {
      const errData = await response.json();
      errorMsg = errData.detail || errData.message || errorMsg;
    } catch {
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

export async function startDebate(topic, maxTurns = 20, proposerModel = 'openai/gpt-oss-120b', opponentModel = 'deepseek/deepseek-v3.2') {
  return fetchJSON('/start-debate', {
    method: 'POST',
    body: JSON.stringify({
      topic,
      max_turns: maxTurns,
      proposer_model: proposerModel,
      opponent_model: opponentModel,
    }),
  });
}

export async function nextTurn(debateId) {
  return fetchJSON('/next-turn', {
    method: 'POST',
    body: JSON.stringify({ debate_id: debateId }),
  });
}

export async function getTranscript(debateId) {
  return fetchJSON(`/transcript/${debateId}`);
}

export async function getDebateSummary(debateId) {
  return fetchJSON(`/summary/${debateId}`);
}
