// Models offered for each debater, grouped by provider. `short` is the display name in the arena.
export const MODEL_GROUPS = [
  {
    name: 'Groq LPU — fastest',
    models: [
      { id: 'openai/gpt-oss-120b', label: 'GPT-OSS 120B (default Proposer)', short: 'GPT-OSS 120B' },
      { id: 'openai/gpt-oss-20b', label: 'GPT-OSS 20B', short: 'GPT-OSS 20B' },
      { id: 'qwen/qwen3.8-27b', label: 'Qwen 3.8 27B', short: 'Qwen 3.8 27B' },
    ],
  },
  {
    name: 'OpenRouter',
    models: [
      { id: 'deepseek/deepseek-v3.2', label: 'DeepSeek V3.2 (default Opponent)', short: 'DeepSeek V3.2' },
      { id: 'deepseek/deepseek-r1-0528', label: 'DeepSeek R1 (reasoning, slower)', short: 'DeepSeek R1' },
      { id: 'meta-llama/llama-3.3-70b-instruct', label: 'Llama 3.3 70B Instruct', short: 'Llama 3.3 70B' },
      { id: 'qwen/qwen-2.5-72b-instruct', label: 'Qwen 2.5 72B Instruct', short: 'Qwen 2.5 72B' },
    ],
  },
  {
    name: 'Google Gemini',
    models: [
      { id: 'gemini-3.6-flash', label: 'Gemini 3.6 Flash', short: 'Gemini 3.6 Flash' },
      { id: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash', short: 'Gemini 3.5 Flash' },
      { id: 'gemini-3.1-flash-lite', label: 'Gemini 3.1 Flash Lite', short: 'Gemini 3.1 Flash Lite' },
    ],
  },
  {
    name: 'NVIDIA NIM',
    models: [
      { id: 'nvidia/llama-3.3-nemotron-super-49b-v1', label: 'Nemotron Super 49B', short: 'Nemotron 49B' },
      { id: 'meta/llama-3.1-8b-instruct', label: 'Llama 3.1 8B', short: 'Llama 3.1 8B' },
    ],
  },
];

export const DEFAULT_PROPOSER = 'openai/gpt-oss-120b';
export const DEFAULT_OPPONENT = 'deepseek/deepseek-v3.2';

export function formatModelName(id) {
  if (!id) return 'AI agent';
  for (const group of MODEL_GROUPS) {
    const model = group.models.find(m => m.id === id);
    if (model) return model.short;
  }
  return id.split('/').pop();
}
