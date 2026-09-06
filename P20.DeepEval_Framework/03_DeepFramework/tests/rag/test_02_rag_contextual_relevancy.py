"""02 - Contextual Relevancy: of what was retrieved, how much is on-topic?

Large chunks drag this down: if a chunk about the refund window also contains
three unrelated sentences, only part of it counts as relevant.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_GOLDENS
from metrics_catalog import SPEC_CONTEXTUAL_RELEVANCY


@pytest.mark.rag
@pytest.mark.retrieval
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("golden", RAG_GOLDENS, ids=lambda g: g.input[:45])
def test_rag_contextual_relevancy(rag_answer, judge, golden):
    reply, ctx = rag_answer(golden.input)
    tc = SPEC_CONTEXTUAL_RELEVANCY.build_case(golden, (reply, ctx))
    assert_test(tc, [SPEC_CONTEXTUAL_RELEVANCY.build_metric(judge)])
