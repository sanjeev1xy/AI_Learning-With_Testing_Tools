"""Runtime configuration loaded from environment / Streamlit secrets.

Nothing in this module prints or logs raw secret values.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from .exceptions import ConfigurationError

load_dotenv()


def _hydrate_from_streamlit_secrets() -> None:
    """Copy flat string secrets from st.secrets into os.environ (Cloud deploys).

    Never overrides an existing env var and never raises.
    """
    try:
        import streamlit as st  # noqa: PLC0415

        for key, value in dict(st.secrets).items():
            if isinstance(value, str) and key not in os.environ:
                os.environ[key] = value
    except Exception:  # noqa: BLE001 - secrets are optional
        pass


_hydrate_from_streamlit_secrets()

_TRUE = {"1", "true", "yes", "on"}


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        return int(raw) if raw not in (None, "") else default
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    try:
        return float(raw) if raw not in (None, "") else default
    except ValueError:
        return default


def _json_env(name: str, default):
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


@dataclass(frozen=True)
class LLMConfig:
    model: str
    api_key: str
    base_url: str
    temperature: float
    max_tokens: int
    provider_label: str
    reasoning_effort: str = ""

    @property
    def configured(self) -> bool:
        return bool(self.model and self.api_key)


@dataclass(frozen=True)
class JiraRestConfig:
    url: str
    auth_mode: str
    email: str
    api_token: str
    bearer_token: str
    api_version: str
    acceptance_criteria_field: str
    include_comments: bool
    max_comments: int

    @property
    def configured(self) -> bool:
        if not self.url:
            return False
        if self.auth_mode == "bearer":
            return bool(self.bearer_token)
        return bool(self.email and self.api_token)


@dataclass(frozen=True)
class JiraMCPConfig:
    transport: str
    url: str
    command: str
    args: list[str]
    headers: dict[str, str]
    get_issue_tool: str
    timeout_seconds: int

    @property
    def configured(self) -> bool:
        if self.transport in {"streamable_http", "sse", "http"}:
            return bool(self.url)
        return bool(self.command)


@dataclass(frozen=True)
class AppConfig:
    app_name: str
    app_env: str
    output_dir: Path
    integration_mode: str
    demo_mode: bool
    demo_allow_synthetic: bool
    max_tickets: int
    max_retries: int
    max_rpm: int
    ticket_timeout_seconds: int
    jira_key_pattern: str
    llm: LLMConfig
    rest: JiraRestConfig
    mcp: JiraMCPConfig
    warnings: list[str] = field(default_factory=list)

    # -- readiness helpers -------------------------------------------------
    @property
    def live_jira_available(self) -> bool:
        if self.integration_mode == "mcp":
            return self.mcp.configured
        if self.integration_mode == "rest":
            return self.rest.configured
        return self.mcp.configured or self.rest.configured

    def effective_demo_mode(self) -> bool:
        """Demo mode is a purely explicit switch (`DEMO_MODE`, default false).

        When true, fixtures are always used; when false, live providers are always
        used and a live failure raises a typed error — demo data is never an
        automatic fallback for a failed live integration.
        """
        return self.demo_mode

    def readiness(self) -> dict[str, object]:
        return {
            "llm_configured": self.llm.configured,
            "llm_model": self.llm.model or "(unset)",
            "llm_provider": self.llm.provider_label,
            "jira_mcp_configured": self.mcp.configured,
            "jira_rest_configured": self.rest.configured,
            "integration_mode": self.integration_mode,
            "live_jira_available": self.live_jira_available,
            "demo_mode_enabled": self.demo_mode,
            "effective_demo_mode": self.effective_demo_mode(),
            "output_dir": str(self.output_dir),
        }


def _load() -> AppConfig:
    warnings: list[str] = []

    integration_mode = _env("JIRA_INTEGRATION_MODE", default="auto").lower()
    if integration_mode not in {"auto", "mcp", "rest"}:
        warnings.append(f"Unknown JIRA_INTEGRATION_MODE '{integration_mode}', defaulting to 'auto'.")
        integration_mode = "auto"

    # LLM: prefer generic vars, fall back to this repo's existing Groq vars.
    llm_model = _env("LLM_MODEL", "GROQ_MODEL")
    llm_key = _env("LLM_API_KEY", "GROQ_API_KEY", "SANJEEV_GROQ_CREWAI_API_KEY", "OPENAI_API_KEY")
    llm_base = _env("LLM_BASE_URL", "BASE_URL", "GROQ_BASE_URL")
    provider_label = "unknown"
    if llm_base:
        if "groq" in llm_base:
            provider_label = "groq"
        elif "deepseek" in llm_base:
            provider_label = "deepseek"
        elif "openai" in llm_base:
            provider_label = "openai"
    elif llm_model.startswith("gpt-"):
        provider_label = "openai"

    llm = LLMConfig(
        model=llm_model,
        api_key=llm_key,
        base_url=llm_base,
        temperature=_float("LLM_TEMPERATURE", 0.1),
        max_tokens=_int("LLM_MAX_TOKENS", 4000),
        provider_label=provider_label,
        reasoning_effort=_env("LLM_REASONING_EFFORT"),
    )
    if not llm.configured:
        warnings.append("LLM is not configured (set LLM_MODEL and LLM_API_KEY). CrewAI cannot run without it.")

    rest = JiraRestConfig(
        url=_env("JIRA_URL").rstrip("/"),
        auth_mode=_env("JIRA_AUTH_MODE", default="basic").lower(),
        email=_env("JIRA_EMAIL", "JIRA_USERNAME"),
        api_token=_env("JIRA_API_TOKEN"),
        bearer_token=_env("JIRA_BEARER_TOKEN"),
        api_version=_env("JIRA_API_VERSION", default="3"),
        acceptance_criteria_field=_env("JIRA_ACCEPTANCE_CRITERIA_FIELD"),
        include_comments=_bool("JIRA_INCLUDE_COMMENTS", False),
        max_comments=_int("JIRA_MAX_COMMENTS", 20),
    )

    mcp = JiraMCPConfig(
        transport=_env("JIRA_MCP_TRANSPORT", default="streamable_http").lower(),
        url=_env("JIRA_MCP_URL"),
        command=_env("JIRA_MCP_COMMAND"),
        args=list(_json_env("JIRA_MCP_ARGS_JSON", [])),
        headers=dict(_json_env("JIRA_MCP_HEADERS_JSON", {})),
        get_issue_tool=_env("JIRA_MCP_GET_ISSUE_TOOL"),
        timeout_seconds=_int("JIRA_MCP_TIMEOUT_SECONDS", 20),
    )

    demo_mode = _bool("DEMO_MODE", False)

    config = AppConfig(
        app_name=_env("APP_NAME", default="Jira QA Crew"),
        app_env=_env("APP_ENV", default="development"),
        output_dir=Path(_env("OUTPUT_DIR", default="outputs")).resolve(),
        integration_mode=integration_mode,
        demo_mode=demo_mode,
        demo_allow_synthetic=_bool("DEMO_ALLOW_SYNTHETIC", True),
        max_tickets=_int("PIPELINE_MAX_TICKETS", 20),
        max_retries=max(0, _int("PIPELINE_MAX_RETRIES", 2)),
        max_rpm=max(1, _int("PIPELINE_MAX_RPM", 3)),
        ticket_timeout_seconds=_int("PIPELINE_TICKET_TIMEOUT_SECONDS", 600),
        jira_key_pattern=_env("JIRA_KEY_PATTERN", default=r"[A-Z][A-Z0-9_]+-\d+"),
        llm=llm,
        rest=rest,
        mcp=mcp,
        warnings=warnings,
    )

    if not config.live_jira_available and not demo_mode and integration_mode != "auto":
        warnings.append(
            f"Integration mode '{integration_mode}' selected but that provider is not configured."
        )
    return config


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return _load()


def reload_config() -> AppConfig:
    """Re-read the environment (used by tests and the UI 'reload' control).

    Does not override variables already present in ``os.environ`` — an explicit
    environment / Streamlit secret always wins over the ``.env`` file.
    """
    load_dotenv(override=False)
    _hydrate_from_streamlit_secrets()
    get_config.cache_clear()
    return get_config()


def require_llm(config: AppConfig | None = None) -> LLMConfig:
    cfg = config or get_config()
    if not cfg.llm.configured:
        raise ConfigurationError(
            "LLM credentials are not configured. Set LLM_MODEL and LLM_API_KEY in .env."
        )
    return cfg.llm
