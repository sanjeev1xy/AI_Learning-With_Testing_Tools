"""Jira MCP provider (primary path).

Uses the official ``mcp`` Python SDK when available. The provider decision is
made by :class:`JiraGateway`, never by an LLM. This class only knows how to
talk to one MCP server over stdio or streamable HTTP and call a single
read-only "get issue" tool.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from ..config import JiraMCPConfig
from ..exceptions import JiraProviderUnavailableError, JiraTransportError
from ..logging_utils import get_logger, redact
from .adf import adf_to_text
from .base import JiraIssue, JiraProvider

logger = get_logger("jira.mcp")

# Candidate tool names across the common Jira MCP servers.
_DEFAULT_TOOL_CANDIDATES = ("jira_get_issue", "getJiraIssue", "get_issue", "jira.getIssue", "issue_get")
# Only these tools are ever allowed to be invoked.
_READ_ONLY_ALLOW = set(_DEFAULT_TOOL_CANDIDATES) | {"jira_search", "search"}


def _mcp_available() -> bool:
    try:
        import mcp  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


class JiraMCPProvider(JiraProvider):
    name = "MCP"

    def __init__(self, config: JiraMCPConfig) -> None:
        self._cfg = config

    # -- lifecycle ----------------------------------------------------
    async def _session(self):
        """Yield an initialised MCP ClientSession as an async context manager."""
        from contextlib import asynccontextmanager

        from mcp import ClientSession

        @asynccontextmanager
        async def _ctx():
            if self._cfg.transport in {"streamable_http", "http", "sse"}:
                from mcp.client.streamable_http import streamablehttp_client

                async with streamablehttp_client(self._cfg.url, headers=self._cfg.headers or None) as (r, w, _):
                    async with ClientSession(r, w) as session:
                        await session.initialize()
                        yield session
            else:
                from mcp import StdioServerParameters
                from mcp.client.stdio import stdio_client

                params = StdioServerParameters(command=self._cfg.command, args=self._cfg.args)
                async with stdio_client(params) as (r, w):
                    async with ClientSession(r, w) as session:
                        await session.initialize()
                        yield session

        return _ctx()

    async def _resolve_tool(self, session) -> str:
        if self._cfg.get_issue_tool:
            return self._cfg.get_issue_tool
        listed = await session.list_tools()
        names = {t.name for t in listed.tools}
        for candidate in _DEFAULT_TOOL_CANDIDATES:
            if candidate in names:
                return candidate
        raise JiraTransportError(
            f"MCP server exposes no recognised get-issue tool. Set JIRA_MCP_GET_ISSUE_TOOL. Saw: {sorted(names)}"
        )

    async def _fetch_async(self, key: str) -> dict[str, Any]:
        ctx = await self._session()
        async with ctx as session:
            tool = await self._resolve_tool(session)
            if tool not in _READ_ONLY_ALLOW and tool != self._cfg.get_issue_tool:
                raise JiraProviderUnavailableError(f"Refusing to call non-allowlisted MCP tool '{tool}'.")
            for arg_name in ("issue_key", "issueIdOrKey", "key", "issue"):
                try:
                    result = await asyncio.wait_for(
                        session.call_tool(tool, {arg_name: key}), timeout=self._cfg.timeout_seconds
                    )
                    return _extract_payload(result)
                except Exception as exc:  # noqa: BLE001 - try the next argument spelling
                    last = exc
            raise JiraTransportError(f"MCP get-issue call failed: {redact(str(last))}")

    def _run(self, coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        # Already inside a loop (rare in this app) — use a private loop.
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    # -- interface --------------------------------------------------
    def health_check(self) -> bool:
        if not self._cfg.configured or not _mcp_available():
            return False
        try:

            async def _check():
                ctx = await self._session()
                async with ctx as session:
                    await session.list_tools()
                return True

            return bool(self._run(asyncio.wait_for(_check(), timeout=self._cfg.timeout_seconds)))
        except Exception as exc:  # noqa: BLE001
            logger.info("MCP health check failed: %s", redact(str(exc)))
            return False

    def fetch_issue(self, key: str) -> JiraIssue:
        if not self._cfg.configured:
            raise JiraProviderUnavailableError("Jira MCP is not configured (missing URL or command).")
        if not _mcp_available():
            raise JiraProviderUnavailableError("The 'mcp' Python package is not installed.")
        payload = self._run(self._fetch_async(key))
        return _issue_from_payload(key, payload)


def _extract_payload(result: Any) -> dict[str, Any]:
    content = getattr(result, "content", None)
    if content:
        for block in content:
            text = getattr(block, "text", None)
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"summary": "", "description": text}
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    raise JiraTransportError("MCP tool returned an empty or unparseable response.")


def _issue_from_payload(key: str, payload: dict[str, Any]) -> JiraIssue:
    fields = payload.get("fields", payload)

    def _name(v):
        return v.get("name", "") if isinstance(v, dict) else (v or "")

    issue = JiraIssue(
        key=(payload.get("key") or key).upper(),
        summary=fields.get("summary", "") or payload.get("summary", ""),
        description=adf_to_text(fields.get("description") or payload.get("description")),
        issue_type=_name(fields.get("issuetype") or fields.get("issue_type")),
        status=_name(fields.get("status")),
        priority=_name(fields.get("priority")),
        labels=list(fields.get("labels", []) or []),
        components=[_name(c) for c in (fields.get("components", []) or [])],
        parent=_name(fields.get("parent")) or (fields.get("parent", {}) or {}).get("key", "")
        if isinstance(fields.get("parent"), dict)
        else "",
        subtasks=[s.get("key", "") for s in (fields.get("subtasks", []) or []) if isinstance(s, dict)],
        acceptance_criteria=adf_to_text(fields.get("acceptance_criteria") or payload.get("acceptance_criteria")),
        url=payload.get("url", ""),
        source="MCP",
    )
    if not issue.summary and not issue.description:
        raise JiraTransportError("MCP payload contained no usable issue data.")
    return issue
