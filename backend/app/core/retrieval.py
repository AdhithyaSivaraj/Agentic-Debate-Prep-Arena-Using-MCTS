"""
retrieval.py — Embedding-Based Fact Retrieval (Unit II: Informed/Semantic Search)

This module satisfies the syllabus Unit II "search" requirement using embedding-based
semantic similarity search — a priority/similarity-driven retrieval mechanism that is
analogous to best-first search over a semantic space.

=== HOW IT WORKS ===

1. At debate setup time, call `build_index(facts, embed_fn)` once.
   This embeds all facts using the provided embedding function and caches the
   resulting vectors in the module's global state.

2. During each debate turn, call `retrieve_relevant_fact(query, top_k)`.
   This embeds the query, computes cosine similarity against all cached fact vectors,
   and returns the top-k most semantically relevant facts.

=== DESIGN DECISIONS ===

- `cosine_similarity(a, b)` is implemented manually using numpy (dot product / norms).
  No heavy vector-DB dependency — the fact base is small (20–25 facts per debate),
  making a full linear scan perfectly efficient.

- The embedding function is INJECTED rather than hardcoded. This serves two purposes:
    (a) Tests can pass a fake embedding function without needing an API key.
    (b) The embedding model can be swapped without changing retrieval logic.

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

import re
import zlib
from dataclasses import dataclass
from typing import Callable

import numpy as np


EmbedFn = Callable[[list[str]], np.ndarray]


@dataclass
class RetrievedFact:
    """A fact retrieved from the index, with its similarity score."""
    text: str
    score: float
    index: int


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
        self.vectors: np.ndarray = vectors

    def __len__(self) -> int:
        return len(self.facts)


_FACT_INDEX: FactIndex | None = None


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

    row_norms = np.linalg.norm(matrix, axis=1)

    row_norms = np.where(row_norms == 0.0, 1e-10, row_norms)

    dot_products = matrix @ query_vec
    return (dot_products / (row_norms * query_norm)).astype(float)


def build_index(facts: list[str], embed_fn: EmbedFn) -> FactIndex:
    """
    Embed all facts and cache them in the module-level FactIndex.

    Call this ONCE at debate setup time (after fact_generation.py produces the fact list).
    The resulting index is stored globally and used by all subsequent
    retrieve_relevant_fact() calls within the same session.

    Args:
        facts:    List of fact strings (the local fact base for this debate).
        embed_fn: A function that takes a list of strings and returns a 2D numpy
                  array of embeddings. In tests, a fake function can be injected.

    Returns:
        The constructed FactIndex (also stored globally for retrieval calls).

    Raises:
        ValueError: if facts is empty.
    """
    global _FACT_INDEX

    if not facts:
        raise ValueError("build_index requires at least one fact")

    vectors = embed_fn(facts)
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

    query_vec = np.array(embed_fn([query]), dtype=float)[0]

    scores = cosine_similarity_matrix(query_vec, fact_index.vectors)

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


_STOPWORDS = frozenset(
    "a an and are as at be been but by can could do does for from has have how if in into is it its "
    "may might more most no not of on or should so than that the their them then there these they this "
    "to was were what when which while who will with would".split()
)


def _tokens(text: str) -> list[str]:
    """Lowercase word tokens with CamelCase split (so atom names match prose) and stopwords removed."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return [t for t in re.findall(r"[a-z0-9]+", spaced.lower()) if t not in _STOPWORDS and len(t) > 1]


def hashed_bow_embed(texts: list[str], dim: int = 512) -> np.ndarray:
    """
    Local, deterministic embedding: hashed bag of words with sublinear term frequency,
    L2-normalised. Cosine similarity between these vectors measures shared vocabulary,
    which is what fact retrieval needs within a single debate's fact base.
    """
    vecs = np.zeros((len(texts), dim), dtype=float)
    for row, text in enumerate(texts):
        for tok in _tokens(text):
            vecs[row, zlib.crc32(tok.encode()) % dim] += 1.0
        vecs[row] = np.log1p(vecs[row])
        norm = np.linalg.norm(vecs[row])
        if norm > 0:
            vecs[row] /= norm
    return vecs
