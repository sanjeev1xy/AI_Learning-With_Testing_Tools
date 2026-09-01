"""Atlassian Document Format (ADF) -> readable plain text.

Handles the node types that show up in real Jira Cloud descriptions. Unknown
nodes degrade gracefully to their text content.
"""

from __future__ import annotations

from typing import Any


def _render_nodes(nodes: list[dict[str, Any]], depth: int = 0) -> str:
    return "".join(_render_node(n, depth) for n in nodes or [])


def _render_node(node: dict[str, Any], depth: int = 0) -> str:  # noqa: C901 - explicit dispatch is clearer here
    if not isinstance(node, dict):
        return ""
    node_type = node.get("type", "")
    content = node.get("content", []) or []

    if node_type == "text":
        text = node.get("text", "")
        marks = {m.get("type") for m in node.get("marks", []) or []}
        if "code" in marks:
            text = f"`{text}`"
        if "strong" in marks:
            text = f"**{text}**"
        return text

    if node_type == "hardBreak":
        return "\n"

    if node_type == "paragraph":
        return _render_nodes(content, depth) + "\n\n"

    if node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        return f"{'#' * int(level)} {_render_nodes(content, depth).strip()}\n\n"

    if node_type in {"bulletList", "orderedList"}:
        ordered = node_type == "orderedList"
        lines = []
        for idx, item in enumerate(content, start=1):
            marker = f"{idx}." if ordered else "-"
            inner = _render_nodes(item.get("content", []), depth + 1).strip()
            inner = inner.replace("\n\n", "\n")
            pad = "  " * depth
            lines.append(f"{pad}{marker} {inner}")
        return "\n".join(lines) + "\n\n"

    if node_type == "listItem":
        return _render_nodes(content, depth)

    if node_type == "codeBlock":
        return "```\n" + _render_nodes(content, depth) + "\n```\n\n"

    if node_type == "blockquote":
        inner = _render_nodes(content, depth).strip()
        return "\n".join(f"> {line}" for line in inner.splitlines()) + "\n\n"

    if node_type == "rule":
        return "---\n\n"

    if node_type == "table":
        return _render_table(content) + "\n"

    if node_type in {"tableRow", "tableCell", "tableHeader"}:
        return _render_nodes(content, depth)

    if node_type == "mediaSingle" or node_type == "media":
        return "[media attachment]\n\n"

    if node_type in {"mention", "emoji"}:
        attrs = node.get("attrs", {})
        return attrs.get("text") or attrs.get("shortName") or ""

    if node_type == "inlineCard" or node_type == "blockCard":
        return node.get("attrs", {}).get("url", "") + "\n"

    # Fallback: just render children.
    return _render_nodes(content, depth)


def _render_table(rows: list[dict[str, Any]]) -> str:
    rendered: list[list[str]] = []
    for row in rows:
        cells = row.get("content", []) or []
        rendered.append([_render_nodes(c.get("content", []), 0).strip().replace("\n", " ") for c in cells])
    if not rendered:
        return ""
    lines = ["| " + " | ".join(rendered[0]) + " |", "| " + " | ".join("---" for _ in rendered[0]) + " |"]
    for row in rendered[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def adf_to_text(value: Any) -> str:
    """Convert an ADF document (or a plain string) into readable text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        if value.get("type") == "doc":
            return _render_nodes(value.get("content", []), 0).strip()
        if "content" in value:
            return _render_nodes(value.get("content", []), 0).strip()
        return str(value.get("text", "")).strip()
    if isinstance(value, list):
        return _render_nodes(value, 0).strip()
    return str(value).strip()
