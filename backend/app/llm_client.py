"""
llm_client.py — Single entry point for every LLM call in the backend.

Routes a model name to its provider (Groq LPU, OpenRouter, NVIDIA NIM, or Gemini),
retries once on rate limits, walks the provider's fallback models, and returns plain
text. The LLM is only ever used for language: fact-base generation, candidate claim
phrasing, and the post-debate debrief. Contradictions and move selection are decided
by resolution.py and mcts.py.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_FALLBACKS,
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL_FALLBACKS,
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    NVIDIA_MODEL_FALLBACKS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL_FALLBACKS,
)

logger = logging.getLogger(__name__)


class LLMUnavailable(RuntimeError):
    """Raised when no configured provider could produce a response."""


def is_gemini_model(model_name: str) -> bool:
    return bool(model_name) and model_name.lower().startswith("gemini")


def is_openrouter_model(model_name: str) -> bool:
    if not model_name:
        return False
    m = model_name.lower()
    return m.startswith("meta-llama/") or m.startswith("deepseek/") or m.startswith("qwen/qwen-2.5") or "openrouter" in m


def is_groq_model(model_name: str) -> bool:
    if not model_name or is_openrouter_model(model_name):
        return False
    m = model_name.lower()
    return any(k in m for k in ["gpt-oss", "qwen3.8", "groq", "versatile", "instant"])


def provider_for(model_name: str) -> tuple[str, str, str, list[str]]:
    """Return (provider, base_url, api_key, fallback_models) for a model name."""
    if is_gemini_model(model_name):
        return "gemini", "", GEMINI_API_KEY, GEMINI_MODEL_FALLBACKS
    if is_openrouter_model(model_name):
        return "openrouter", OPENROUTER_BASE_URL, OPENROUTER_API_KEY, OPENROUTER_MODEL_FALLBACKS
    if is_groq_model(model_name):
        return "groq", GROQ_BASE_URL, GROQ_API_KEY, GROQ_MODEL_FALLBACKS
    return "nvidia", NVIDIA_BASE_URL, NVIDIA_API_KEY, NVIDIA_MODEL_FALLBACKS


def _strip_reasoning(text: str) -> str:
    """Drop <think>/<thought> scratchpads that reasoning models emit before the answer."""
    for tag in ("think", "thought"):
        if f"<{tag}>" in text.lower():
            if f"</{tag}>" in text.lower():
                text = re.sub(rf"<{tag}>.*?</{tag}>", "", text, flags=re.DOTALL | re.IGNORECASE)
            else:
                text = ""
    return text.strip()


def complete(
    model_name: str,
    system: str,
    user: str,
    json_mode: bool = False,
    temperature: float = 0.6,
    timeout: float = 30.0,
    reasoning_effort: str = "low",
) -> str:
    """
    One request to exactly one model. Raises on any provider error or empty output.
    reasoning_effort applies to gpt-oss models ("low" | "medium" | "high").
    """
    provider, base_url, api_key, _ = provider_for(model_name)
    if not api_key:
        raise LLMUnavailable(f"No API key configured for {provider} (model '{model_name}').")

    if provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json" if json_mode else None,
        )
        response = client.models.generate_content(model=model_name, contents=user, config=config)
        text = response.text or ""
    else:
        from openai import OpenAI

        client = OpenAI(base_url=base_url, api_key=api_key)
        extra: dict[str, Any] = {}
        if json_mode:
            extra["response_format"] = {"type": "json_object"}
        if "gpt-oss" in model_name:
            # gpt-oss otherwise spends the default output budget on reasoning and truncates the answer
            extra["reasoning_effort"] = reasoning_effort
            extra["max_completion_tokens"] = 8000
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            timeout=timeout,
            **extra,
        )
        msg = response.choices[0].message
        text = msg.content or getattr(msg, "reasoning", None) or ""

    text = _strip_reasoning(text)
    if not text:
        raise LLMUnavailable(f"Empty response from '{model_name}'.")
    return text


def complete_with_fallbacks(
    model_name: str,
    system: str,
    user: str,
    json_mode: bool = False,
    temperature: float = 0.6,
    timeout: float = 30.0,
    reasoning_effort: str = "low",
) -> tuple[str, str]:
    """
    Try `model_name`, then the other models of the same provider.
    Each model gets one retry after a rate limit. Returns (text, model_used).
    """
    _, _, _, fallbacks = provider_for(model_name)
    models = [model_name] + [m for m in fallbacks if m != model_name]
    errors: list[str] = []
    for model in models:
        for attempt in range(2):
            try:
                return complete(model, system, user, json_mode, temperature, timeout, reasoning_effort), model
            except LLMUnavailable as e:
                errors.append(str(e))
                break
            except Exception as e:
                err = str(e)
                errors.append(f"{model}: {err[:200]}")
                rate_limited = "429" in err or "rate" in err.lower() or "quota" in err.lower()
                quota_exhausted = "exceeded your current quota" in err.lower()
                if rate_limited and not quota_exhausted and attempt == 0:
                    logger.warning(f"Rate limit on '{model}', retrying in 3s...")
                    time.sleep(3)
                    continue
                logger.warning(f"LLM call failed on '{model}' ({err[:200]}). Trying next model...")
                break
    raise LLMUnavailable("; ".join(errors) or f"All models failed for '{model_name}'.")


def available_default_models() -> list[str]:
    """One default model per provider that has an API key, in preference order."""
    defaults = []
    if GROQ_API_KEY:
        defaults.append(GROQ_MODEL_FALLBACKS[0])
    if GEMINI_API_KEY:
        defaults.append(GEMINI_MODEL_FALLBACKS[0])
    if OPENROUTER_API_KEY:
        defaults.append(OPENROUTER_MODEL_FALLBACKS[0])
    if NVIDIA_API_KEY:
        defaults.append(NVIDIA_MODEL_FALLBACKS[0])
    return defaults


def complete_any(
    preferred_model: str | None,
    system: str,
    user: str,
    json_mode: bool = False,
    temperature: float = 0.6,
    timeout: float = 30.0,
) -> tuple[str, str]:
    """Try the preferred model's provider first, then every other configured provider."""
    candidates = [preferred_model] if preferred_model else []
    preferred_provider = provider_for(preferred_model)[0] if preferred_model else None
    candidates += [m for m in available_default_models() if provider_for(m)[0] != preferred_provider]
    errors: list[str] = []
    for model in candidates:
        try:
            return complete_with_fallbacks(model, system, user, json_mode, temperature, timeout)
        except LLMUnavailable as e:
            errors.append(str(e))
    raise LLMUnavailable("; ".join(errors) or "No LLM provider is configured.")


def parse_json_payload(text: str) -> Any:
    """Parse a JSON object or array out of an LLM response (tolerates fences and surrounding prose)."""
    cleaned = _strip_reasoning(text)
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start, end = cleaned.find(open_ch), cleaned.rfind(close_ch)
        if start != -1 and end > start:
            snippet = cleaned[start : end + 1]
            for attempt in (snippet, re.sub(r",\s*([\]}])", r"\1", snippet)):
                try:
                    return json.loads(attempt)
                except json.JSONDecodeError:
                    continue
    raise ValueError(f"Response is not valid JSON (first 300 chars): {text[:300]}")


def clean_claim_text(text: str) -> str:
    """
    Strip LLM meta-text prefixes ("The generated claim is:", "Agent A:"), reasoning
    scratchpads, and surrounding quotes, leaving only the substantive claim.
    """
    if not text:
        return ""
    s = text.strip()
    for tag in ("think", "thought"):
        if f"<{tag}>" in s.lower():
            if f"</{tag}>" in s.lower():
                s = re.sub(rf"<{tag}>.*?</{tag}>", "", s, flags=re.DOTALL | re.IGNORECASE).strip()
            else:
                parts = re.split(rf"<{tag}>", s, flags=re.IGNORECASE)
                s = parts[-1].strip() if len(parts) > 1 and parts[-1].strip() else parts[0].strip()
    s = re.sub(r"^(thinking process|thought|internal reasoning):.*?\n+", "", s, flags=re.IGNORECASE | re.DOTALL).strip()

    meta_patterns = [
        r"^(the|a)\s+(generated|proposed|final|selected)\s+(claim|response|answer|rebuttal|argument|point)\s+(is|says|states)?:?\s*",
        r"^here\s+is\s+the\s+(claim|response|rebuttal|argument|point):?\s*",
        r"^this\s+response\s+is\s+a\s+continuation[^\n]*\n*",
        r"^as\s+the\s+(proposer|opponent|agent\s+[ab]):?\s*",
        r"^agent\s+[ab]:?\s*",
        r"^claim:?\s*",
        r"^rebuttal:?\s*",
    ]
    for pat in meta_patterns:
        s = re.sub(pat, "", s, flags=re.IGNORECASE | re.MULTILINE).strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    for pat in meta_patterns:
        s = re.sub(pat, "", s, flags=re.IGNORECASE | re.MULTILINE).strip()
    return s


def humanize_logic(text: str, vocabulary: set[str]) -> str:
    """
    Rewrite leaked logic notation as prose: known atom names become words
    ("LabSecurityWired" → "lab security wired") and →, ¬, ∨ become "leads to", "not", "or".
    """
    if not text:
        return text
    for atom_name in sorted(vocabulary, key=len, reverse=True):
        if atom_name in text:
            words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", atom_name).lower()
            text = re.sub(rf"\b{re.escape(atom_name)}\b", words, text)
    text = re.sub(r"\s*(→|->)\s*", " leads to ", text)
    text = re.sub(r"¬\s*", "not ", text)
    text = re.sub(r"\s*∨\s*", " or ", text)
    return text
