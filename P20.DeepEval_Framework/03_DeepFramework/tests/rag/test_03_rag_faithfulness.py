"""03 - Faithfulness: is every claim in the answer backed by a retrieved chunk?

This is the metric RAG exists to pass. A low score means the generator went
beyond its evidence — the classic RAG failure.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_GOLDENS
from metrics_catalog import SPEC_FAITHFULNESS


@pytest.mark.rag
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("golden", RAG_GOLDENS, ids=lambda g: g.input[:45])
def test_rag_faithfulness(rag_answer, judge, golden):
    reply, ctx = rag_answer(golden.input)
    tc = SPEC_FAITHFULNESS.build_case(golden, (reply, ctx))
    assert_test(tc, [SPEC_FAITHFULNESS.build_metric(judge)])
