"""
tool_schemas.py — Shared OpenAI-Function-Calling-Compatible Tool Schemas

CRITICAL CONSTRAINT (must never be violated):
    Both GeminiAgent and NemotronAgent must use the EXACT SAME tool schemas.
    This file is the single source of truth — no duplicated or drifted tool logic
    between the two agent files. Both APIs (Google Gemini native function calling
    and OpenRouter/OpenAI-compatible) accept this format.

=== THE FOUR TOOLS ===

1. retrieve_relevant_fact   — semantic search; returns grounding fact from local fact base
2. check_contradiction      — runs resolution.py; returns whether KB is unsatisfiable
3. select_best_rebuttal     — runs MCTS; returns chosen rebuttal + rejected alternatives
4. generate_claim           — the ONLY tool where the LLM freely generates language

=== FORMAT ===

Each schema follows the OpenAI function-calling JSON format:
{
    "name":        str           — the tool name the LLM will call
    "description": str           — explains purpose and when to call (guides LLM's tool-use decisions)
    "parameters": {
        "type": "object",
        "properties": { ... },   — each parameter with type + description
        "required": [ ... ]      — list of required parameter names
    }
}

This format is:
- Natively supported by Gemini (via google-generativeai SDK's Tool/FunctionDeclaration)
- Supported by OpenRouter/Nemotron via the OpenAI-compatible /v1/chat/completions endpoint
  with the standard "tools" field.

=== CONVERSION NOTES FOR GEMINI ===

The google-generativeai SDK accepts function declarations as dicts in this exact format
when passed to genai.GenerativeModel(tools=[...]). No conversion needed.

=== CONVERSION NOTES FOR OPENROUTER (NEMOTRON) ===

Pass directly as the "tools" list in the OpenAI chat completions body:
    {"tools": [{"type": "function", "function": schema} for schema in TOOL_SCHEMAS]}
"""

                                                                             
RETRIEVE_RELEVANT_FACT_SCHEMA = {
    "name": "retrieve_relevant_fact",
    "description": (
        "Search the local debate fact base for the most relevant fact to ground your next claim. "
        "You MUST call this tool before generating any new claim or rebuttal. "
        "The retrieved fact gives you a logically verified foundation for your argument — "
        "do not make claims without grounding them in a retrieved fact first. "
        "This tool performs semantic similarity search over the pre-built fact index; "
        "it does NOT make any web requests or generate new information."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "claim_topic": {
                "type": "string",
                "description": (
                    "A short phrase or sentence describing the topic of the claim you intend to make. "
                    "E.g., 'effect of exams on student mental health' or 'economic impact of automation'. "
                    "This is used as the search query to find the most relevant fact."
                ),
            },
            "top_k": {
                "type": "integer",
                "description": (
                    "Number of relevant facts to retrieve (default 1). "
                    "Use 1 for normal claim generation. "
                    "Use 2–3 if you want to consider multiple facts before choosing a direction."
                ),
            },
        },
        "required": ["claim_topic"],
    },
}

                                                                             
CHECK_CONTRADICTION_SCHEMA = {
    "name": "check_contradiction",
    "description": (
        "Run the propositional resolution algorithm to check whether any claims in the knowledge base "
        "are logically contradictory. You MUST call this after asserting any new claim — "
        "both to check your own consistency and to detect if the opponent has contradicted themselves. "
        "This tool runs a deterministic algorithm (propositional resolution refutation); "
        "it does NOT ask an LLM whether something 'sounds contradictory'. "
        "If a contradiction is found, the response includes a proof trace showing exactly which "
        "clauses conflict — use this to form your rebuttal."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "enum": ["self", "opponent", "combined"],
                "description": (
                    "'self'     — check your own knowledge base for internal contradictions. "
                    "'opponent' — check the opponent's knowledge base for their self-contradictions. "
                    "'combined' — check whether your claims contradict the opponent's claims "
                    "             (cross-agent logical conflict). "
                    "Check 'self' after every turn. Check 'opponent' and 'combined' when looking "
                    "for attack vectors against the opponent."
                ),
            },
            "agent_id": {
                "type": "string",
                "description": (
                    "Your agent identifier: 'agent_a' or 'agent_b'. "
                    "Used to look up the correct knowledge base."
                ),
            },
        },
        "required": ["target", "agent_id"],
    },
}

                                                                             
SELECT_BEST_REBUTTAL_SCHEMA = {
    "name": "select_best_rebuttal",
    "description": (
        "Use Monte Carlo Tree Search to select the strongest rebuttal from a list of candidates. "
        "You MUST call this tool whenever you are responding to an attack or a detected contradiction — "
        "do NOT pick a rebuttal yourself based on intuition. "
        "The MCTS algorithm evaluates candidates by simulating future exchanges and scoring them "
        "by how many opponent contradictions they force versus how many own vulnerabilities they create. "
        "The tool returns the chosen rebuttal AND the rejected alternatives with their scores — "
        "this 'show your work' output is displayed to the audience in the UI."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "candidates": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of 3–5 candidate rebuttal strings to evaluate. "
                    "These should be rough phrasings of possible next moves — "
                    "the actual final phrasing will be done by generate_claim() after MCTS selects one. "
                    "Must have at least 2 candidates for MCTS to be meaningful."
                ),
            },
            "agent_id": {
                "type": "string",
                "description": "Your agent identifier: 'agent_a' or 'agent_b'.",
            },
            "n_simulations": {
                "type": "integer",
                "description": (
                    "Number of MCTS simulations to run (default 10). "
                    "Higher = more thorough selection but slower. "
                    "10 is sufficient for a 3–5 candidate list."
                ),
            },
        },
        "required": ["candidates", "agent_id"],
    },
}

                                                                             
GENERATE_CLAIM_SCHEMA = {
    "name": "generate_claim",
    "description": (
        "Generate a fluent, natural-language argument or rebuttal to speak in the debate. "
        "This is the ONLY tool where you produce new language — all other tools run algorithms. "
        "You should call this LAST in each turn, after: "
        "(1) retrieve_relevant_fact, (2) check_contradiction, "
        "(3) select_best_rebuttal (if responding to an attack). "
        "The claim you generate must be grounded in the retrieved fact and consistent with "
        "the MCTS-selected direction. Keep claims focused and logically structured."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "context": {
                "type": "string",
                "description": (
                    "The full debate context: topic, your role, the opponent's last claim, "
                    "and the grounding fact retrieved from retrieve_relevant_fact. "
                    "Format: 'Topic: <topic>. Your role: <proposer/opponent>. "
                    "Opponent last said: <claim>. Grounding fact: <fact>.'"
                ),
            },
            "direction": {
                "type": "string",
                "description": (
                    "The strategic direction for this claim — either the MCTS-selected rebuttal "
                    "candidate text (when responding to an attack) or a brief description of "
                    "the argument angle you want to make (when opening a turn). "
                    "The generated claim must follow this direction closely."
                ),
            },
            "propositional_form": {
                "type": "string",
                "description": (
                    "The propositional clause form of this claim for assertion into the knowledge base. "
                    "Must be in the format: 'A → B' (implication), '¬A' (negation), or 'A' (assertion). "
                    "E.g., 'ExamsAbolished → StressReduced' or '¬ExamsBeneficial'. "
                    "This is parsed by the system — use only simple atom names (CamelCase, no spaces)."
                ),
            },
            "agent_id": {
                "type": "string",
                "description": "Your agent identifier: 'agent_a' or 'agent_b'.",
            },
        },
        "required": ["context", "direction", "propositional_form", "agent_id"],
    },
}

                                                                             
TOOL_SCHEMAS: list[dict] = [
    RETRIEVE_RELEVANT_FACT_SCHEMA,
    CHECK_CONTRADICTION_SCHEMA,
    SELECT_BEST_REBUTTAL_SCHEMA,
    GENERATE_CLAIM_SCHEMA,
]

                                           
TOOL_SCHEMA_BY_NAME: dict[str, dict] = {s["name"]: s for s in TOOL_SCHEMAS}

                                                                             
def as_openai_tools(schemas: list[dict] = TOOL_SCHEMAS) -> list[dict]:
    """
    Wrap schemas in the OpenAI chat-completions "tools" format:
        [{"type": "function", "function": schema}, ...]

    Use this when constructing the request body for OpenRouter (Nemotron).
    Gemini's SDK accepts the raw schema dicts directly — do NOT wrap for Gemini.
    """
    return [{"type": "function", "function": s} for s in schemas]
