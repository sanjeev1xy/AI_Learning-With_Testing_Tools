"""05 - Hallucination: does the answer contradict known ground truth?

Scored against `context` (what is actually true), not `retrieval_context`
(what the bot was handed). A RAG bot can be faithful to a stale chunk and
still be wrong about the world.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_GOLDENS
from metrics_catalog import SPEC_HALLUCINATION


@pytest.mark.rag
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("golden", RAG_GOLDENS, ids=lambda g: g.input[:45])
def test_rag_hallucination(rag_answer, judge, golden):
    reply, _ = rag_answer(golden.input)
    tc = SPEC_HALLUCINATION.build_case(golden, reply)
    assert_test(tc, [SPEC_HALLUCINATION.build_metric(judge)])
