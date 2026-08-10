"""
retrieval.py — Embedding-Based Fact Retrieval (Unit II: Informed/Semantic Search)

This module satisfies the syllabus Unit II "search" requirement using embedding-based
semantic similarity search — a priority/similarity-driven retrieval mechanism that is
analogous to best-first search over a semantic space.

=== HOW IT WORKS ===

1. At debate setup time, call `build_index(facts, embed_fn)` once.
   This embeds all facts using the provided embedding function (Nemotron 3 Embed 1B
   via OpenRouter in production) and caches the resulting vectors in the module's
   global state.

2. During each debate turn, call `retrieve_relevant_fact(query, top_k)`.
   This embeds the query, computes cosine similarity against all cached fact vectors,
   and returns the top-k most semantically relevant facts.

=== DESIGN DECISIONS ===

- `cosine_similarity(a, b)` is implemented manually using numpy (dot product / norms).
  No heavy vector-DB dependency — the fact base is small (20–25 facts per debate),
  making a full linear scan perfectly efficient.

- The embedding function is INJECTED rather than hardcoded. This serves two purposes:
    (a) Tests can pass a fake embedding function without needing an API key.
    (b) The production embedding function (Nemotron via OpenRouter) can be swapped
        for any other embedding model without changing retrieval logic.

- The module maintains a global cache (`_FACT_INDEX`) so embedding is done once per
  debate session, not once per retrieval call.

- `retrieve_relevant_fact()` returns ranked facts with their similarity scores,
  not just raw text — the scores are included for potential UI display and debugging.

=== UNIT II CONNECTION ===

Semantic similarity search is the embedding-space analogue of best-first / informed
search: the "heuristic" is the cosine similarity score, and we always expand (return)
the node (fact) with the highest score relative to the current query. This is
explicitly defensible as a Unit II algorithm in the project report.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

# An embedding function: takes a list of strings, returns a 2D numpy array
# of shape (n_strings, embedding_dim).
EmbedFn = Callable[[list[str]], np.ndarray]


@dataclass
class RetrievedFact:
    """A fact retrieved from the index, with its similarity score."""
    text: str
    score: float    # cosine similarity in [−1, 1], higher = more relevant
    index: int      # position in the original fact list (for debugging)


# ---------------------------------------------------------------------------
# Global fact index (per-session cache)
# ---------------------------------------------------------------------------

class FactIndex:
    """
    In-memory index of facts and their embedding vectors.
    Created once per debate session by calling `build_index()`.
    """

    def __init__(self, facts: list[str], vectors: np.ndarray):
        """
        Args:
            facts:   The original fact strings (parallel to vectors).
            vectors: 2D numpy array of shape (len(facts), embedding_dim).
        """
        if len(facts) != vectors.shape[0]:
            raise ValueError(
                f"facts ({len(facts)}) and vectors ({vectors.shape[0]}) must have the same length"
            )
        self.facts: list[str] = facts
        self.vectors: np.ndarray = vectors   # shape: (n_facts, embedding_dim)

    def __len__(self) -> int:
        return len(self.facts)


# Module-level singleton — replaced each time build_index() is called
_FACT_INDEX: FactIndex | None = None


# ---------------------------------------------------------------------------
# Core math: cosine similarity
# ---------------------------------------------------------------------------

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1D embedding vectors.

    cosine_similarity(a, b) = (a · b) / (||a|| * ||b||)

    Returns a float in [−1, 1]:
        1.0  → identical direction (most similar)
        0.0  → orthogonal (no semantic relationship)
       −1.0  → opposite direction (most dissimilar)

    Edge case: if either vector is the zero vector (norm == 0),
    returns 0.0 to avoid division by zero.

    Implementation: manual numpy only — no vector DB, no sklearn.
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def cosine_similarity_matrix(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between a single query vector and every row in a matrix.

    Args:
        query_vec: 1D array of shape (embedding_dim,)
        matrix:    2D array of shape (n_facts, embedding_dim)

    Returns:
        1D array of shape (n_facts,) — similarity score for each fact.

    This is a batch version of cosine_similarity(), vectorised for efficiency
    even though at MVP scale (~20 facts) the difference is negligible.
    """
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0.0:
        return np.zeros(matrix.shape[0])

    row_norms = np.linalg.norm(matrix, axis=1)          # shape: (n_facts,)
    # Avoid division by zero for zero-vector rows
    row_norms = np.where(row_norms == 0.0, 1e-10, row_norms)

    dot_products = matrix @ query_vec                    # shape: (n_facts,)
    return (dot_products / (row_norms * query_norm)).astype(float)


# ---------------------------------------------------------------------------
# Index construction
# ---------------------------------------------------------------------------

def build_index(facts: list[str], embed_fn: EmbedFn) -> FactIndex:
    """
    Embed all facts and cache them in the module-level FactIndex.

    Call this ONCE at debate setup time (after fact_generation.py produces the fact list).
    The resulting index is stored globally and used by all subsequent
    retrieve_relevant_fact() calls within the same session.

    Args:
        facts:    List of fact strings (the local fact base for this debate).
        embed_fn: A function that takes a list of strings and returns a 2D numpy
                  array of embeddings. In production this calls Nemotron 3 Embed 1B
                  via OpenRouter. In tests, a fake function can be injected.

    Returns:
        The constructed FactIndex (also stored globally for retrieval calls).

    Raises:
        ValueError: if facts is empty.
    """
    global _FACT_INDEX

    if not facts:
        raise ValueError("build_index requires at least one fact")

    vectors = embed_fn(facts)           # shape: (len(facts), embedding_dim)
    vectors = np.array(vectors, dtype=float)

    _FACT_INDEX = FactIndex(facts=facts, vectors=vectors)
    return _FACT_INDEX


def get_index() -> FactIndex:
    """
    Return the current module-level FactIndex.
    Raises RuntimeError if build_index() has not been called yet.
    """
    if _FACT_INDEX is None:
        raise RuntimeError(
            "FactIndex is not built. Call build_index(facts, embed_fn) first."
        )
    return _FACT_INDEX


def clear_index() -> None:
    """
    Clear the module-level FactIndex.
    Useful between debate sessions or in tests to ensure isolation.
    """
    global _FACT_INDEX
    _FACT_INDEX = None


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve_relevant_fact(
    query: str,
    embed_fn: EmbedFn,
    top_k: int = 1,
    index: FactIndex | None = None,
) -> list[RetrievedFact]:
    """
    Retrieve the top-k most semantically relevant facts for a given query.

    This is the function both agents call (via tool_executor) before making a claim.
    It embeds the query, computes cosine similarity against all cached fact vectors,
    and returns the top-k facts sorted by descending similarity score.

    Args:
        query:    The natural-language query string (typically the topic of the next claim).
        embed_fn: Embedding function — same signature as in build_index().
                  Must produce vectors of the same dimensionality as the index.
        top_k:    Number of facts to return (default 1 — the single most relevant fact).
        index:    Explicitly pass a FactIndex to use (for testing).
                  If None, uses the module-level global index.

    Returns:
        List of RetrievedFact objects, sorted by descending similarity score.
        Length is min(top_k, len(index)).

    Raises:
        RuntimeError: if no index is available and `index` argument is also None.
        ValueError:   if top_k < 1.
    """
    if top_k < 1:
        raise ValueError(f"top_k must be >= 1, got {top_k}")

    fact_index = index if index is not None else get_index()

    # Embed the query — embed_fn takes a list, returns a 2D array; take row 0
    query_vec = np.array(embed_fn([query]), dtype=float)[0]  # shape: (embedding_dim,)

    # Compute cosine similarity against all cached fact vectors
    scores = cosine_similarity_matrix(query_vec, fact_index.vectors)  # shape: (n_facts,)

    # Rank by descending score and take top-k
    k = min(top_k, len(fact_index))
    top_indices = np.argsort(scores)[::-1][:k]

    return [
        RetrievedFact(
            text=fact_index.facts[i],
            score=round(float(scores[i]), 6),
            index=int(i),
        )
        for i in top_indices
    ]


# ---------------------------------------------------------------------------
# Production embedding function (Nemotron 3 Embed 1B via OpenRouter)
# ---------------------------------------------------------------------------

def make_nemotron_embed_fn(api_key: str) -> EmbedFn:
    """
    Factory that returns a production embedding function using Nemotron 3 Embed 1B
    via the OpenRouter API (OpenAI-compatible endpoint).

    The returned function takes a list of strings and returns a 2D numpy array
    of embeddings — the same signature expected by build_index() and
    retrieve_relevant_fact().

    Args:
        api_key: OpenRouter API key (loaded from config.py / .env — never hardcoded).

    Returns:
        An EmbedFn suitable for passing to build_index() and retrieve_relevant_fact().

    Note:
        This function makes a REAL HTTP call. Do not call it in unit tests —
        inject a fake embed_fn instead (see tests/test_retrieval.py for examples).
    """
    import httpx

    OPENROUTER_EMBED_URL = "https://openrouter.ai/api/v1/embeddings"
    # Verified free-tier embedding model on OpenRouter:
    NEMOTRON_EMBED_MODEL = "nvidia/nemo-embed-qa-e5-v5"

    def embed_fn(texts: list[str]) -> np.ndarray:
        """
        Batch-embed a list of strings using Nemotron 3 Embed 1B.
        Returns a 2D numpy array of shape (len(texts), embedding_dim).
        """
        response = httpx.post(
            OPENROUTER_EMBED_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": NEMOTRON_EMBED_MODEL,
                "input": texts,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        # OpenAI-compatible response: {"data": [{"embedding": [...], "index": 0}, ...]}
        embeddings = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
        return np.array(embeddings, dtype=float)

    return embed_fn
