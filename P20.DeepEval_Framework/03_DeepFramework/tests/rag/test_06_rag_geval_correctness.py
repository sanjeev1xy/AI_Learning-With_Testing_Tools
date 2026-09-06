"""06 - Correctness (G-Eval): does the grounded answer match the reference?

Wording is free; the figures (7 business days, $9.99, 30 days, IPX4) must be
right. Judged by rubric against the golden answer.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_GOLDENS
from metrics_catalog import SPEC_CORRECTNESS


@pytest.mark.rag
@pytest.mark.geval
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("golden", RAG_GOLDENS, ids=lambda g: g.input[:45])
def test_rag_geval_correctness(rag_answer, judge, golden):
    reply, _ = rag_answer(golden.input)
    tc = SPEC_CORRECTNESS.build_case(golden, reply)
    assert_test(tc, [SPEC_CORRECTNESS.build_metric(judge)])
