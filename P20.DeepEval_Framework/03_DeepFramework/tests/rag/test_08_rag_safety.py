"""08 - RAG Safety: loaded, off-corpus, and injection prompts.

The grounded bot should stay neutral and in-domain: no bias / toxicity, no
medical-financial-legal advice, no prompt disclosure, and it should decline
anything outside the ShopSphere knowledge base rather than answer from thin air.
"""
import pytest
from deepeval import assert_test

from datasets.rag_goldens import RAG_SAFETY_PROMPTS
from metrics_catalog import SPEC_RAG_SAFETY


@pytest.mark.rag
@pytest.mark.safety
@pytest.mark.security
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("prompt", RAG_SAFETY_PROMPTS, ids=lambda p: p[:45])
def test_rag_safety(rag_answer, judge, prompt):
    reply, _ = rag_answer(prompt)
    tc = SPEC_RAG_SAFETY.build_case(prompt, reply)
    assert_test(tc, [SPEC_RAG_SAFETY.build_metric(judge)])
