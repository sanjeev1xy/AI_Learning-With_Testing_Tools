"""10 - Conversational: multi-turn against the RAG chat endpoint.

Replays a scripted conversation turn by turn, then scores the whole thread
for completeness (did the replies satisfy the running intent?) and knowledge
retention (did later replies use facts established earlier?).
"""
import pytest
from deepeval import assert_test
from deepeval.test_case import ConversationalTestCase, Turn

from datasets.rag_goldens import RAG_CONVERSATIONS
from metrics_catalog import (
    BOT_ROLE,
    SPEC_CONVERSATION_COMPLETENESS,
    SPEC_KNOWLEDGE_RETENTION,
)


def _run(rag, convo) -> ConversationalTestCase:
    turns = []
    for msg in convo["user_turns"]:
        turns.append(Turn(role="user", content=msg))
        turns.append(Turn(role="assistant", content=rag.chat(msg).reply))
    return ConversationalTestCase(turns=turns, scenario=convo["scenario"], chatbot_role=BOT_ROLE)


@pytest.mark.rag
@pytest.mark.conversational
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("convo", RAG_CONVERSATIONS, ids=lambda c: c["name"])
def test_rag_conversation_completeness(rag, judge, convo):
    tc = _run(rag, convo)
    assert_test(tc, [SPEC_CONVERSATION_COMPLETENESS.build_metric(judge)])


@pytest.mark.rag
@pytest.mark.conversational
@pytest.mark.slow
@pytest.mark.needs_rag
@pytest.mark.parametrize("convo", RAG_CONVERSATIONS, ids=lambda c: c["name"])
def test_rag_knowledge_retention(rag, judge, convo):
    tc = _run(rag, convo)
    assert_test(tc, [SPEC_KNOWLEDGE_RETENTION.build_metric(judge)])
