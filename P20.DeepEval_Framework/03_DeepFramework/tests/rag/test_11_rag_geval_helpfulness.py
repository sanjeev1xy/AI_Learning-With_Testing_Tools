"""11 - Helpfulness (G-Eval): is the answer complete, direct, and actionable?

Faithful and correct is not enough if the reply buries the one figure the
customer needs, or punts them to email for something the corpus answers.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_GOLDENS
from metrics_catalog import SPEC_RAG_HELPFULNESS


@pytest.mark.rag
@pytest.mark.geval
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("golden", RAG_GOLDENS, ids=lambda g: g.input[:45])
def test_rag_geval_helpfulness(rag_answer, judge, golden):
    reply, _ = rag_answer(golden.input)
    tc = SPEC_RAG_HELPFULNESS.build_case(golden, reply)
    assert_test(tc, [SPEC_RAG_HELPFULNESS.build_metric(judge)])
