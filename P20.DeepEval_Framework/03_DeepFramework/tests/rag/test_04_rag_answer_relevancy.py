"""04 - Answer Relevancy: does the grounded answer address the question?

Retrieval can be perfect and the answer still wander. This scores only the
final reply against the input, ignoring the context.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_GOLDENS
from metrics_catalog import SPEC_ANSWER_RELEVANCY


@pytest.mark.rag
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("golden", RAG_GOLDENS, ids=lambda g: g.input[:45])
def test_rag_answer_relevancy(rag_answer, judge, golden):
    reply, _ = rag_answer(golden.input)
    tc = SPEC_ANSWER_RELEVANCY.build_case(golden, reply)
    assert_test(tc, [SPEC_ANSWER_RELEVANCY.build_metric(judge)])
