"""
test_retrieval.py — Unit tests for the embedding-based fact retrieval module.
Phase 3: all tests use FAKE embedding functions — no real API calls required.

The fake embed_fn returns deterministic embeddings so we can know exactly which
fact should be retrieved for a given query.

Design principle: retrieval.py's embedding function is injected, not hardcoded,
precisely so these tests can run without network access or API keys.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
import numpy as np
from core.retrieval import (
    cosine_similarity,
    cosine_similarity_matrix,
    build_index,
    retrieve_relevant_fact,
    get_index,
    clear_index,
    FactIndex,
    RetrievedFact,
)


# ===========================================================================
# Fake embedding functions for tests (no API calls)
# ===========================================================================

def make_identity_embed_fn(dim: int = 4):
    """
    Returns an embed_fn where each text is mapped to a one-hot vector.
    Text at position i gets a 1 at index (i % dim).
    Two texts with the same position mod dim will have cosine_similarity = 1.0.
    """
    call_count = [0]

    def embed_fn(texts: list[str]) -> np.ndarray:
        vecs = []
        for text in texts:
            vec = np.zeros(dim)
            vec[call_count[0] % dim] = 1.0
            call_count[0] += 1
            vecs.append(vec)
        return np.array(vecs)

    return embed_fn


def make_fixed_embed_fn(mapping: dict[str, list[float]]):
    """
    Returns an embed_fn that uses a fixed string→vector mapping.
    Any text not in the mapping gets a zero vector.
    This gives us full control over similarity scores in tests.
    """
    def embed_fn(texts: list[str]) -> np.ndarray:
        vecs = []
        for text in texts:
            vecs.append(mapping.get(text, [0.0] * 4))
        return np.array(vecs, dtype=float)
    return embed_fn


# ===========================================================================
# Tests for cosine_similarity
# ===========================================================================

class TestCosineSimilarity:
    def test_identical_vectors_score_one(self):
        a = np.array([1.0, 0.0, 0.0])
        assert cosine_similarity(a, a) == pytest.approx(1.0, abs=1e-9)

    def test_orthogonal_vectors_score_zero(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        assert cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-9)

    def test_opposite_vectors_score_minus_one(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([-1.0, 0.0, 0.0])
        assert cosine_similarity(a, b) == pytest.approx(-1.0, abs=1e-9)

    def test_zero_vector_returns_zero(self):
        """Division by zero guard: zero vector should return 0.0."""
        a = np.array([0.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        assert cosine_similarity(a, b) == 0.0

    def test_both_zero_vectors_returns_zero(self):
        a = np.array([0.0, 0.0, 0.0])
        assert cosine_similarity(a, a) == 0.0

    def test_returns_float(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([4.0, 5.0, 6.0])
        assert isinstance(cosine_similarity(a, b), float)

    def test_known_value(self):
        """
        For a = [1, 1, 0] and b = [1, 0, 0]:
        cosine = (1*1 + 1*0 + 0*0) / (sqrt(2) * 1) = 1/sqrt(2) ≈ 0.7071
        """
        a = np.array([1.0, 1.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        expected = 1.0 / np.sqrt(2)
        assert cosine_similarity(a, b) == pytest.approx(expected, rel=1e-6)

    def test_magnitude_does_not_matter(self):
        """Cosine similarity is invariant to vector magnitude."""
        a = np.array([1.0, 0.0])
        b = np.array([100.0, 0.0])
        assert cosine_similarity(a, b) == pytest.approx(1.0, abs=1e-9)


# ===========================================================================
# Tests for cosine_similarity_matrix
# ===========================================================================

class TestCosineSimilarityMatrix:
    def test_shape_is_n_rows(self):
        query = np.array([1.0, 0.0, 0.0])
        matrix = np.eye(3)
        scores = cosine_similarity_matrix(query, matrix)
        assert scores.shape == (3,)

    def test_best_match_has_highest_score(self):
        """Query = [1, 0, 0] → row 0 is the best match."""
        query = np.array([1.0, 0.0, 0.0])
        matrix = np.eye(3)
        scores = cosine_similarity_matrix(query, matrix)
        assert np.argmax(scores) == 0

    def test_zero_query_returns_zero_scores(self):
        query = np.zeros(3)
        matrix = np.eye(3)
        scores = cosine_similarity_matrix(query, matrix)
        assert np.all(scores == 0.0)

    def test_identical_rows_get_same_score(self):
        query = np.array([1.0, 1.0])
        matrix = np.array([[1.0, 1.0], [1.0, 1.0]])
        scores = cosine_similarity_matrix(query, matrix)
        assert scores[0] == pytest.approx(scores[1], abs=1e-9)


# ===========================================================================
# Tests for build_index
# ===========================================================================

class TestBuildIndex:
    def setup_method(self):
        """Clear any existing index before each test."""
        clear_index()

    def test_build_index_returns_fact_index(self):
        embed_fn = make_fixed_embed_fn({"A": [1.0, 0.0], "B": [0.0, 1.0]})
        idx = build_index(["A", "B"], embed_fn)
        assert isinstance(idx, FactIndex)

    def test_build_index_stores_facts(self):
        facts = ["fact one", "fact two", "fact three"]
        embed_fn = make_fixed_embed_fn({f: [float(i), 0.0] for i, f in enumerate(facts)})
        idx = build_index(facts, embed_fn)
        assert idx.facts == facts

    def test_build_index_length(self):
        facts = ["A", "B", "C"]
        embed_fn = make_fixed_embed_fn({f: [float(i), 0.0] for i, f in enumerate(facts)})
        idx = build_index(facts, embed_fn)
        assert len(idx) == 3

    def test_build_index_empty_raises(self):
        with pytest.raises(ValueError):
            build_index([], make_fixed_embed_fn({}))

    def test_get_index_returns_built_index(self):
        embed_fn = make_fixed_embed_fn({"A": [1.0, 0.0]})
        idx = build_index(["A"], embed_fn)
        assert get_index() is idx

    def test_get_index_before_build_raises(self):
        with pytest.raises(RuntimeError):
            get_index()

    def test_clear_index_removes_index(self):
        embed_fn = make_fixed_embed_fn({"A": [1.0, 0.0]})
        build_index(["A"], embed_fn)
        clear_index()
        with pytest.raises(RuntimeError):
            get_index()


# ===========================================================================
# Tests for retrieve_relevant_fact
# ===========================================================================

class TestRetrieveRelevantFact:
    def setup_method(self):
        clear_index()

    def _make_index(self) -> tuple[FactIndex, dict]:
        """
        Build a 3-fact index with known orthogonal embeddings:
            "about exams"    → [1, 0, 0]
            "about stress"   → [0, 1, 0]
            "about health"   → [0, 0, 1]
        """
        mapping = {
            "about exams":  [1.0, 0.0, 0.0],
            "about stress": [0.0, 1.0, 0.0],
            "about health": [0.0, 0.0, 1.0],
            # queries:
            "exams query":  [1.0, 0.0, 0.0],   # should match "about exams"
            "stress query": [0.0, 1.0, 0.0],   # should match "about stress"
        }
        embed_fn = make_fixed_embed_fn(mapping)
        facts = ["about exams", "about stress", "about health"]
        idx = build_index(facts, embed_fn)
        return idx, mapping

    def test_retrieves_most_similar_fact(self):
        """
        Query aligned with 'about exams' embedding → 'about exams' is top result.
        """
        idx, mapping = self._make_index()
        embed_fn = make_fixed_embed_fn(mapping)
        results = retrieve_relevant_fact("exams query", embed_fn, top_k=1, index=idx)
        assert len(results) == 1
        assert results[0].text == "about exams"

    def test_retrieves_correct_second_fact(self):
        idx, mapping = self._make_index()
        embed_fn = make_fixed_embed_fn(mapping)
        results = retrieve_relevant_fact("stress query", embed_fn, top_k=1, index=idx)
        assert results[0].text == "about stress"

    def test_top_k_returns_k_results(self):
        idx, mapping = self._make_index()
        embed_fn = make_fixed_embed_fn(mapping)
        results = retrieve_relevant_fact("exams query", embed_fn, top_k=3, index=idx)
        assert len(results) == 3

    def test_top_k_capped_at_index_size(self):
        """top_k larger than index size should return all facts."""
        idx, mapping = self._make_index()
        embed_fn = make_fixed_embed_fn(mapping)
        results = retrieve_relevant_fact("exams query", embed_fn, top_k=100, index=idx)
        assert len(results) == 3   # only 3 facts in index

    def test_results_sorted_by_descending_score(self):
        """The first result must always be the highest-scoring one."""
        idx, mapping = self._make_index()
        embed_fn = make_fixed_embed_fn(mapping)
        results = retrieve_relevant_fact("exams query", embed_fn, top_k=3, index=idx)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_result_is_retrieved_fact_instances(self):
        idx, mapping = self._make_index()
        embed_fn = make_fixed_embed_fn(mapping)
        results = retrieve_relevant_fact("exams query", embed_fn, top_k=1, index=idx)
        assert isinstance(results[0], RetrievedFact)

    def test_result_has_score_field(self):
        idx, mapping = self._make_index()
        embed_fn = make_fixed_embed_fn(mapping)
        results = retrieve_relevant_fact("exams query", embed_fn, top_k=1, index=idx)
        assert isinstance(results[0].score, float)

    def test_top_k_zero_raises(self):
        idx, mapping = self._make_index()
        embed_fn = make_fixed_embed_fn(mapping)
        with pytest.raises(ValueError):
            retrieve_relevant_fact("any query", embed_fn, top_k=0, index=idx)

    def test_perfect_match_has_score_near_one(self):
        """When query vector == fact vector, cosine similarity should be ≈ 1.0."""
        idx, mapping = self._make_index()
        embed_fn = make_fixed_embed_fn(mapping)
        results = retrieve_relevant_fact("exams query", embed_fn, top_k=1, index=idx)
        assert results[0].score == pytest.approx(1.0, abs=1e-5)
