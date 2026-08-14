"""
fact_generation.py — One-Time LLM-Based Fact Base Generation

This is the ONLY place in the entire system where new LLM-generated content enters.
During actual debate turns, no new generation occurs — everything runs on the local
fact base produced here plus the classical algorithms.

=== FLOW ===

1. User submits a debate topic (e.g., "Should exams be abolished?")
2. Gemini generates 20–25 factual claims with explicit logical relationships
   (supports / contradicts / implies)
3. Our code normalises the LLM output into strict propositional clause form
   (A → B, ¬A, A) using parse_propositional_form() from tool_executor.py
4. The resulting clauses seed both:
   (a) The resolution KB (via KnowledgeBase.tell())
   (b) The retrieval index (via retrieval.build_index())

=== WHAT THE LLM IS ASKED TO DO ===

The prompt explicitly asks for structured output: each fact must include
- A natural-language sentence
- A propositional form (atom → atom, ¬atom, or atom)
- A relationship type (supports / contradicts / is_independent)

The propositional form is what our algorithms use; the natural-language sentence
is what agents cite when grounding their claims.
"""
from __future__ import annotations

import json
import re

from core.resolution import Clause, clause_to_str


class FactRecord:
    """
    A single fact from the generated fact base.

    Attributes:
        text:             Natural-language sentence (used in retrieval + claim generation)
        propositional:    Propositional clause form as a string (e.g., "Exams → StressHigh")
        clause:           Parsed Clause (frozenset) — None if parsing failed
        relationship:     "supports", "contradicts", or "is_independent"
    """
    __slots__ = ("text", "propositional", "clause", "relationship")

    def __init__(
        self,
        text: str,
        propositional: str,
        clause: Clause | None,
        relationship: str,
    ):
        self.text = text
        self.propositional = propositional
        self.clause = clause
        self.relationship = relationship

    def __repr__(self) -> str:
        clause_str = clause_to_str(self.clause) if self.clause else "UNPARSED"
        return f"FactRecord({clause_str!r}, rel={self.relationship!r})"


FACT_GENERATION_SYSTEM_PROMPT = """You are a logical fact extractor for a debate system.
Your output is consumed by a propositional resolution engine — accuracy of logical form is critical.
Do not add opinions. Generate factual, logically structured claims only."""

def build_fact_generation_prompt(topic: str, n_facts: int = 20) -> str:
    """
    Build the prompt sent to Gemini to generate the fact base for a debate topic.

    The prompt instructs the LLM to produce structured JSON output that our parser
    can normalise into propositional clauses.
    """
    return f"""Generate exactly {n_facts} factual claims about the following debate topic.
Each claim must have an explicit propositional logical form that can be parsed by a theorem prover.

Debate topic: "{topic}"

Output a JSON array of objects. Each object must have these exact keys:
- "text": a clear, factual natural-language sentence (1–2 sentences max)
- "propositional": the logical form using ONLY these formats:
    * "A → B"    (A implies B; use CamelCase atom names, no spaces within names)
    * "¬A"       (A is false / negated)
    * "A"        (A is asserted as true)
    Examples: "ExamsAbolished → StressReduced", "¬ExamsBeneficial", "ExamsTestMemory"
- "relationship": one of "supports_proposition" | "contradicts_proposition" | "is_independent"
  (relative to the general proposition that "{topic}" is a good idea)

Rules:
- Atom names must be CamelCase single tokens (e.g., ExamsAbolished, StressHigh, LearningImproved)
- No spaces within atom names
- Use → for implications, ¬ for negation
- Include a mix of supporting and contradicting facts for a balanced debate
- Facts must be grounded in real-world knowledge, not opinions

Return ONLY the JSON array — no explanation, no markdown fences, no extra text."""


def parse_fact_generation_response(raw_response: str) -> list[FactRecord]:
    """
    Parse the LLM's JSON response into a list of FactRecord objects.

    Handles:
    - Clean JSON arrays
    - JSON embedded in markdown code fences
    - Partial failures (malformed entries are skipped with a warning)

    Returns a list of FactRecord with valid clauses. Records where propositional
    form could not be parsed still have clause=None and are included in the list
    (callers decide whether to skip or keep them).
    """
                                                                             
    from tools.tool_executor import parse_propositional_form

                                      
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
                                               
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned, flags=re.IGNORECASE)
                              
        cleaned = re.sub(r"\n?```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Fact generation response is not valid JSON: {e}\n"
            f"Raw response (first 500 chars): {raw_response[:500]}"
        )

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON array, got {type(data).__name__}"
        )

    records: list[FactRecord] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        text = item.get("text", "").strip()
        propositional = item.get("propositional", "").strip()
        relationship = item.get("relationship", "is_independent").strip()

        if not text or not propositional:
            continue                           

        clause = parse_propositional_form(propositional)

        records.append(FactRecord(
            text=text,
            propositional=propositional,
            clause=clause,
            relationship=relationship,
        ))

    return records


def generate_fact_base(
    topic: str,
    gemini_api_key: str,
    n_facts: int = 20,
    model_name: str = "gemini-3.6-flash",
) -> list[FactRecord]:
    """
    Call Gemini to generate n_facts facts about the topic, then parse + normalise
    the output into FactRecord objects with propositional clause form.

    This is called ONCE per debate session (POST /start-debate).
    After this call, all debate logic uses the local fact base — no further LLM
    fact generation occurs during debate turns.

    Args:
        topic:          The debate topic string.
        gemini_api_key: Google AI Studio API key (from config.py / .env).
        n_facts:        Number of facts to request (default 20).
        model_name:     Gemini model to use (default gemini-2.0-flash, free tier).

    Returns:
        List of FactRecord objects. Records with clause=None were not parseable
        into propositional form (logged as warnings).

    Raises:
        ValueError: if the LLM response cannot be parsed as JSON.
        Exception:  if the Gemini API call fails (caller should handle retry).
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=gemini_api_key)
    prompt = build_fact_generation_prompt(topic, n_facts=n_facts)
    config = types.GenerateContentConfig(
        system_instruction=FACT_GENERATION_SYSTEM_PROMPT
    )

    response = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            break
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "quota" in err_str.lower()) and attempt < 2:
                import time
                time.sleep(4)
            else:
                raise e

    if not response:
        raise RuntimeError("Failed to generate facts from Gemini API.")

    raw_text = response.text
    records = parse_fact_generation_response(raw_text)
    return records


def extract_fact_texts(records: list[FactRecord]) -> list[str]:
    """Return just the natural-language strings (for build_index in retrieval.py)."""
    return [r.text for r in records]


def extract_valid_clauses(records: list[FactRecord]) -> list[Clause]:
    """Return only clauses that parsed successfully (for KnowledgeBase seeding)."""
    return [r.clause for r in records if r.clause is not None]


def generate_fact_base_openai(
    topic: str,
    api_key: str,
    base_url: str,
    model_name: str,
    n_facts: int = 20,
) -> list[FactRecord]:
    """
    Call OpenAI-compatible provider (Groq LPU, NVIDIA NIM) to generate n_facts facts about topic.
    """
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key)
    prompt = build_fact_generation_prompt(topic, n_facts=n_facts)

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": FACT_GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
        timeout=15.0,
    )

    content = response.choices[0].message.content or ""
    return parse_fact_generation_response(content)
