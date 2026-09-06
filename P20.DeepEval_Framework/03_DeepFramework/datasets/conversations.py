"""Multi-turn golden conversations for the conversational metrics.

Each entry is an ordered list of (role, content) turns. The USER turns are
replayed against the live chatbot; the ASSISTANT turns here are reference
context only — the metric scores what the bot actually says.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversationGolden:
    name: str
    scenario: str
    user_turns: list[str]
    categories: list[str] = field(default_factory=list)


CONVERSATION_GOLDENS: list[ConversationGolden] = [
    ConversationGolden(
        name="refund_then_shipping",
        scenario="A customer asks about the refund window, then follows up about return shipping cost without repeating context.",
        user_turns=[
            "What is your refund window?",
            "And who pays for the return shipping?",
            "Does that change if the item arrived damaged?",
        ],
        categories=["policy"],
    ),
    ConversationGolden(
        name="product_carryover",
        scenario="A customer asks about a product, then asks a follow-up that only makes sense if the bot remembered which product.",
        user_turns=[
            "Tell me about the SP-EARBUDS-01.",
            "What's the battery life on those again?",
            "Are they waterproof enough for the gym?",
        ],
        categories=["product"],
    ),
    ConversationGolden(
        name="order_then_account",
        scenario="A customer switches topic mid-conversation from shipping speed to account recovery.",
        user_turns=[
            "How long does express shipping take?",
            "Okay. Separately, I can't log in — how do I reset my password?",
            "Can I also turn on two-factor while I'm in there?",
        ],
        categories=["shipping", "account"],
    ),
]
