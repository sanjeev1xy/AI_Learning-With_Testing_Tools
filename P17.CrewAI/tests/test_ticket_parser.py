from __future__ import annotations

import pytest

from jira_qa_crew.exceptions import TicketInputError
from jira_qa_crew.services.ticket_parser import parse_ticket_input


def test_splits_on_all_separators():
    p = parse_ticket_input("VWO-48, VWO-49; VWO-50\nVWO-51 VWO-52")
    assert p.valid == ["VWO-48", "VWO-49", "VWO-50", "VWO-51", "VWO-52"]


def test_normalises_case_and_dedupes():
    p = parse_ticket_input("vwo-48, VWO-48, Vwo-48 abc-1")
    assert p.valid == ["VWO-48", "ABC-1"]
    assert p.duplicates == ["VWO-48"]


def test_rejects_invalid_tokens():
    p = parse_ticket_input("VWO-48, notaticket, 123, FOO")
    assert p.valid == ["VWO-48"]
    assert set(p.invalid) == {"NOTATICKET", "123", "FOO"}


def test_truncates_to_max():
    raw = ", ".join(f"VWO-{i}" for i in range(1, 30))
    p = parse_ticket_input(raw, max_tickets=5)
    assert len(p.valid) == 5
    assert p.truncated is True


def test_empty_and_oversized():
    with pytest.raises(TicketInputError):
        parse_ticket_input(None)
    with pytest.raises(TicketInputError):
        parse_ticket_input("x" * 10_001)
