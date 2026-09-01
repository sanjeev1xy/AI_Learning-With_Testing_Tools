"""Parse, normalise, validate and de-duplicate user-supplied Jira ticket IDs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..config import get_config
from ..exceptions import TicketInputError

_SPLIT_RE = re.compile(r"[\s,;]+")


@dataclass
class ParsedTickets:
    valid: list[str] = field(default_factory=list)
    invalid: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    truncated: bool = False

    @property
    def has_valid(self) -> bool:
        return bool(self.valid)


def parse_ticket_input(
    raw: str,
    *,
    key_pattern: str | None = None,
    max_tickets: int | None = None,
) -> ParsedTickets:
    """Split on comma / space / newline / semicolon, upper-case, dedupe, validate."""
    if raw is None:
        raise TicketInputError("No ticket input provided.")
    cfg = get_config()
    pattern = re.compile(rf"^{key_pattern or cfg.jira_key_pattern}$")
    limit = max_tickets or cfg.max_tickets

    if len(raw) > 10_000:
        raise TicketInputError("Ticket input is too large (>10000 characters).")

    tokens = [t.strip().upper() for t in _SPLIT_RE.split(raw) if t.strip()]

    result = ParsedTickets()
    seen: set[str] = set()
    for token in tokens:
        if not pattern.match(token):
            if token not in result.invalid:
                result.invalid.append(token)
            continue
        if token in seen:
            if token not in result.duplicates:
                result.duplicates.append(token)
            continue
        seen.add(token)
        result.valid.append(token)

    if len(result.valid) > limit:
        result.truncated = True
        result.valid = result.valid[:limit]

    return result
