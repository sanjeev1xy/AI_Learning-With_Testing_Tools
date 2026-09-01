from __future__ import annotations

from jira_qa_crew.jira.adf import adf_to_text


def test_plain_string_passthrough():
    assert adf_to_text("hello world") == "hello world"


def test_headings_paragraphs_lists():
    doc = {
        "type": "doc",
        "content": [
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Steps"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "Do the thing."}]},
            {
                "type": "orderedList",
                "content": [
                    {"type": "listItem", "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": "one"}]}]},
                    {"type": "listItem", "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": "two"}]}]},
                ],
            },
        ],
    }
    text = adf_to_text(doc)
    assert "## Steps" in text
    assert "Do the thing." in text
    assert "1. one" in text and "2. two" in text


def test_marks_and_unknown_nodes():
    doc = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [
                {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
                {"type": "text", "text": " and "},
                {"type": "text", "text": "code", "marks": [{"type": "code"}]},
            ]},
            {"type": "someFutureNode", "content": [{"type": "text", "text": "still visible"}]},
        ],
    }
    text = adf_to_text(doc)
    assert "**bold**" in text
    assert "`code`" in text
    assert "still visible" in text


def test_none():
    assert adf_to_text(None) == ""
