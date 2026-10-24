"""
fact_generation.py — One-Time LLM-Based Fact Base Generation

At debate start, an LLM generates a structured fact base for the topic. It serves two roles:
    (a) Evidence — agents retrieve relevant facts (retrieval.py) to ground each claim.
    (b) Vocabulary — the facts' propositional atoms are the shared logical language both
        agents must use, so resolution can connect one agent's claims to the other's.

=== FLOW ===

1. User submits a debate topic (e.g., "Should exams be abolished?")
2. The LLM generates ~20 factual claims, each with a propositional form
   (A → B, ¬A, A) and a side (supports / contradicts / independent)
3. parse_propositional_form() normalises each form into a resolution clause
4. Clauses seed the agents' knowledge bases by side; texts seed the retrieval index
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from core.resolution import Clause, clause_to_str, parse_propositional_form
from llm_client import LLMUnavailable, available_default_models, complete_any, complete_with_fallbacks, parse_json_payload

logger = logging.getLogger(__name__)

FACT_MODEL_PREFERENCE = "openai/gpt-oss-120b"


class FactRecord:
    """
    A single fact from the generated fact base.

    Attributes:
        text:             Natural-language sentence (used in retrieval + claim grounding)
        propositional:    Propositional clause form as a string (e.g., "Exams → StressHigh")
        clause:           Parsed Clause (frozenset) — None if parsing failed
        relationship:     "supports_proposition", "contradicts_proposition", or "is_independent"
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


@dataclass
class DebateFrame:
    """What each side defends. A topic like "X or Y?" has no truth value, so it is
    rewritten into an arguable resolution with an explicit position per side."""
    resolution: str
    proposer_position: str
    opponent_position: str


def default_frame(topic: str) -> DebateFrame:
    return DebateFrame(
        resolution=topic,
        proposer_position=f'Argues FOR: "{topic}"',
        opponent_position=f'Argues AGAINST: "{topic}"',
    )


def frame_debate(topic: str) -> DebateFrame:
    """Rewrite the topic into a resolution and two opposing positions; falls back to FOR/AGAINST."""
    prompt = f"""A user entered this debate topic: "{topic}"

Rewrite it as a debate with two clearly opposed sides. If the topic is a choice ("X or Y?",
"X vs Y"), the Proposer defends the first option and the Opponent the second. If it is a yes/no
question or a statement, the Proposer defends "yes" and the Opponent "no".

Return a JSON object:
{{"resolution": "one declarative sentence the Proposer defends, e.g. 'College students should buy a gaming laptop rather than a business laptop.'",
  "proposer_position": "one short sentence: what the Proposer argues",
  "opponent_position": "one short sentence: what the Opponent argues"}}"""
    try:
        raw, _ = complete_any(FACT_MODEL_PREFERENCE, "You frame debates precisely. Output JSON only.", prompt, json_mode=True, timeout=20.0)
        data = parse_json_payload(raw)
        frame = DebateFrame(
            resolution=str(data["resolution"]).strip(),
            proposer_position=str(data["proposer_position"]).strip(),
            opponent_position=str(data["opponent_position"]).strip(),
        )
        if frame.resolution and frame.proposer_position and frame.opponent_position:
            return frame
    except (LLMUnavailable, ValueError, KeyError, TypeError) as e:
        logger.warning(f"Debate framing failed ({str(e)[:200]}); using FOR/AGAINST.")
    return default_frame(topic)


FACT_GENERATION_SYSTEM_PROMPT = """You are a logical fact extractor for a debate system.
Your output is consumed by a propositional resolution engine — accuracy of logical form is critical.
Do not add opinions. Generate factual, logically structured claims only. Output JSON only."""


def build_fact_generation_prompt(topic: str, n_facts: int = 20, frame: DebateFrame | None = None) -> str:
    """Build the prompt asking the LLM for a structured, logically connected fact base."""
    frame = frame or default_frame(topic)
    return f"""Generate exactly {n_facts} factual claims about the following debate.
Each claim must have an explicit propositional logical form that can be parsed by a theorem prover.

Debate topic: "{topic}"
Resolution: "{frame.resolution}"
Proposer: {frame.proposer_position}
Opponent: {frame.opponent_position}

Output a JSON object of the form {{"facts": [...]}}. Each fact object must have these exact keys:
- "text": a clear, specific, factual natural-language sentence (1–2 sentences max)
- "propositional": the logical form using ONLY these formats:
    * "A → B"    (A implies B)
    * "¬A"       (A is false)
    * "A"        (A is true)
    Examples: "ExamsAbolished → StressReduced", "¬ExamsBeneficial", "ExamsTestMemory"
- "relationship": one of "supports_proposition" | "contradicts_proposition" | "is_independent"
  ("supports" = helps the Proposer's position, "contradicts" = helps the Opponent's position)

Rules:
- Atom names must be CamelCase single tokens — no spaces — and must name their subject
  (GamingLaptopHeavy, BusinessLaptopBatteryLong — never a subject-less WeightHeavy or BatteryLong)
- Cover several distinct issues (e.g. cost, performance, reliability, practicality), not just one
- Use 10–15 distinct atoms in total and REUSE them across facts so the facts connect
  (one fact's consequent should be another fact's antecedent)
- At least half of the facts must be plain assertions ("A" or "¬A") — concrete claims
  a theorem prover can refute; use "A → B" for the causal links between them
- Include genuine disagreement: some supporting and contradicting facts must use the same
  atoms with opposite polarity (e.g., "C" vs "¬C", or "A → B" vs "A → ¬B")
- Roughly balance supporting and contradicting facts
- Facts must be grounded in real-world knowledge, not opinions"""


def parse_fact_generation_response(raw_response: str) -> list[FactRecord]:
    """
    Parse the LLM's JSON response into FactRecord objects.

    Accepts a bare array or an object {"facts": [...]}, optionally wrapped in markdown
    fences. Entries missing "text" or "propositional" are skipped; entries whose form
    cannot be parsed are kept with clause=None.

    Raises:
        ValueError: if the response is not valid JSON or contains no fact array.
    """
    data = parse_json_payload(raw_response)
    if isinstance(data, dict):
        data = data.get("facts")
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array of facts, got {type(data).__name__}")

    records: list[FactRecord] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        propositional = str(item.get("propositional", "")).strip()
        relationship = str(item.get("relationship", "is_independent")).strip()
        if not text or not propositional:
            continue
        records.append(FactRecord(
            text=text,
            propositional=propositional,
            clause=parse_propositional_form(propositional),
            relationship=relationship,
        ))
    return records


def generate_fact_base(topic: str, n_facts: int = 20, frame: DebateFrame | None = None) -> tuple[list[FactRecord], str]:
    """
    Generate and parse the fact base, trying the preferred fact model first and then
    every other configured provider. Returns (records, model_used).

    Raises:
        LLMUnavailable: if no provider returned a parseable fact base.
    """
    prompt = build_fact_generation_prompt(topic, n_facts=n_facts, frame=frame)
    models = [FACT_MODEL_PREFERENCE] + [m for m in available_default_models() if m != FACT_MODEL_PREFERENCE]
    errors: list[str] = []
    for model in models:
        try:
            raw, model_used = complete_with_fallbacks(
                model, FACT_GENERATION_SYSTEM_PROMPT, prompt, json_mode=True, timeout=45.0
            )
            records = parse_fact_generation_response(raw)
            if extract_valid_clauses(records):
                return records, model_used
            errors.append(f"{model_used}: no parseable propositional forms")
        except (LLMUnavailable, ValueError) as e:
            errors.append(str(e)[:300])
            logger.warning(f"Fact generation via '{model}' failed ({str(e)[:200]}). Trying next provider...")
    raise LLMUnavailable("; ".join(errors))


def extract_fact_texts(records: list[FactRecord]) -> list[str]:
    """Return just the natural-language strings (for build_index in retrieval.py)."""
    return [r.text for r in records]


def extract_valid_clauses(records: list[FactRecord]) -> list[Clause]:
    """Return only clauses that parsed successfully (for KnowledgeBase seeding)."""
    return [r.clause for r in records if r.clause is not None]
