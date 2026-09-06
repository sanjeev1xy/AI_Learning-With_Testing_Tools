"""09 - Summarization (G-Eval): does the answer condense the context cleanly?

Treats the reply as a summary of retrieval_context. High score = keeps the
facts relevant to the question, invents nothing. Low score = drops a needed
fact or adds a number the chunks never contained.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_GOLDENS
from metrics_catalog import SPEC_RAG_SUMMARIZATION


@pytest.mark.rag
@pytest.mark.geval
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("golden", RAG_GOLDENS, ids=lambda g: g.input[:45])
def test_rag_geval_summarization(rag_answer, judge, golden):
    reply, ctx = rag_answer(golden.input)
    tc = SPEC_RAG_SUMMARIZATION.build_case(golden, (reply, ctx))
    assert_test(tc, [SPEC_RAG_SUMMARIZATION.build_metric(judge)])
