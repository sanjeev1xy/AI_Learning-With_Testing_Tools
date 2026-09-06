"""07 - Citation (G-Eval): does the answer cite the source file per claim?

The RAG prompt asks for inline citations like [refund_policy.md]. This rubric
checks that substantive claims carry a bracketed source that matches a
retrieved chunk — not a hallucinated filename.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_GOLDENS
from metrics_catalog import SPEC_RAG_CITATION


@pytest.mark.rag
@pytest.mark.geval
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("golden", RAG_GOLDENS, ids=lambda g: g.input[:45])
def test_rag_geval_citation(rag_answer, judge, golden):
    reply, ctx = rag_answer(golden.input)
    tc = SPEC_RAG_CITATION.build_case(golden, (reply, ctx))
    assert_test(tc, [SPEC_RAG_CITATION.build_metric(judge)])
