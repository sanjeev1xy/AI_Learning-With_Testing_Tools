"""01 - Contextual Precision: are the most relevant chunks ranked first?

Scores the ORDER of retrieval_context against the reference answer. A high
score means the useful chunks sit at the top; noise, if any, is buried.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_GOLDENS
from metrics_catalog import SPEC_CONTEXTUAL_PRECISION


@pytest.mark.rag
@pytest.mark.retrieval
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("golden", RAG_GOLDENS, ids=lambda g: g.input[:45])
def test_rag_contextual_precision(rag_answer, judge, golden):
    reply, ctx = rag_answer(golden.input)
    tc = SPEC_CONTEXTUAL_PRECISION.build_case(golden, (reply, ctx))
    assert_test(tc, [SPEC_CONTEXTUAL_PRECISION.build_metric(judge)])
