"""Dummy Slack MCP for the reporter agent in 013.

Nothing here ever leaves the process. slack_post_message just appends to an
in-memory log so the pipeline can demonstrate a "post the verdict" stage
without a real Slack workspace or bot token.
"""

from langchain.tools import tool

_sent: list[dict] = []


class _DummySlackMCP:
    """Stands in for a real Slack MCP server connection."""

    @staticmethod
    def connect() -> str:
        return "[DummySlackMCP] connected (no real Slack workspace - messages are only logged)"


@tool
def slack_post_message(channel: str, text: str) -> str:
    """Post one message to a Slack channel, e.g. #qa-automation.

    This is a dummy implementation: the message is recorded in-memory and
    printed, never actually sent to Slack. Use Slack mrkdwn (*bold*, `code`,
    > quote), not markdown tables.
    """
    _sent.append({"channel": channel, "text": text})
    print(f"\n[DUMMY SLACK POST -> {channel}]\n{text}\n")
    return f"Posted to {channel} (simulated, not actually sent)"


def sent_messages() -> list[dict]:
    """Every message slack_post_message has recorded so far this run."""
    return list(_sent)


SLACK_TOOLS = (slack_post_message,)
