# testcase-creator-mcp

MCP server over a VWO manual QA test-case export. One file, all three MCP primitives.

The point of this artifact is the distinction:

| Primitive | Control | Used here for |
|---|---|---|
| **Tools** | model-invoked actions | search, lookup, aggregate — the model decides when to call |
| **Resources** | application-controlled context, addressed by URI | schema and bulk dataset the client pulls into context |
| **Prompts** | user-invoked templates | canned QA workflows the user picks from a menu |

Dataset: `../resource/VWO_test_cases.csv` — 40 rows, 8 columns. Loaded once at import, never re-read per request.

## Install

```bash
cd P15.MCP_Creation_VIBE/testcase-creator-mcp
uv sync
```

Pins `fastmcp==2.14.7` on Python `>=3.11,<3.14`.

## Run

```bash
uv run server.py
```

Stdio transport. It will look idle — that is correct, it is waiting for JSON-RPC on stdin. `Ctrl+C` to stop.

The CSV is resolved relative to `server.py` (`./resource/` then `../resource/`). Override with an env var:

```bash
VWO_TESTCASES_CSV=/path/to/VWO_test_cases.csv uv run server.py
```

## Inspect

```bash
npx -y @modelcontextprotocol/inspector .venv/Scripts/python.exe server.py
```

On macOS/Linux use `.venv/bin/python` instead. Open the printed `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=...` URL — the token is required, a bare `localhost:6274` will not connect.

If it exits with `Proxy Server PORT IS IN USE at port 6277`, another Inspector is already running. Either close it, or pick free ports:

```bash
CLIENT_PORT=6284 SERVER_PORT=6287 npx -y @modelcontextprotocol/inspector .venv/Scripts/python.exe server.py
```

Do **not** use `fastmcp dev server.py`. It builds an ephemeral `uv run --with fastmcp` environment that resolves to the latest FastMCP (3.x), silently ignoring the 2.14.7 pin.

### Verification checklist

**Tools** tab — click *List Tools*, expect 4:

| Tool | Try | Expect |
|---|---|---|
| `search_test_cases` | `module` = `payment & checkout`, leave `query` empty | 5 cases; note the match is case-insensitive |
| `get_test_case` | `test_id` = `VWO-1003` | `TC-00003`, proving jira_id lookup works |
| `test_case_stats` | `group_by` = `priority` | `Medium 13, High 13, Low 9, Critical 4, Blocker 1` |
| `list_facets` | no args | 17 modules, 5 priorities, 16 tags |

Error paths — every one returns a readable message, never a stack trace:
`get_test_case` with `TC-99999`; `search_test_cases` with `module` = `Nope` (lists valid modules) or `query` = `zzzz` (empty result set) or `limit` = `0`.

**Resources** tab — *List Resources* shows 2 static, *List Resource Templates* shows 2 templated:

- `testcases://schema` → 8 columns with types and enum values
- `testcases://all` → all 40 cases
- `testcases://module/{name}` → enter `Mobile App` → 3 cases
- `testcases://case/{test_id}` → enter `TC-00005` → module `Mobile App`

**Prompts** tab — *List Prompts* shows 2:

- `review_test_case` with `test_id` = `TC-00002` → a filled critique prompt containing that case's real steps
- `generate_regression_suite` with `module` = `Payment & Checkout` → a prompt with all 5 cases listed as inventory

## Register with Claude Desktop

`claude_desktop_config.json` — Windows: `%APPDATA%\Claude\claude_desktop_config.json`, macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`.

```json
{
  "mcpServers": {
    "vwo-testcases": {
      "command": "C:\\Users\\sanje\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\Users\\sanje\\AI_Projects_Section\\P15.MCP_Creation_VIBE\\testcase-creator-mcp",
        "run",
        "server.py"
      ]
    }
  }
}
```

Claude Desktop launches the server with no working directory, so `--directory` is required. Use the absolute path to `uv.exe` — Claude Desktop does not inherit your shell `PATH`. Restart Claude Desktop fully (quit from the tray, not just close the window) after editing.

## Known limitation

`review_test_case` and `generate_regression_suite` raise `PromptError` with a specific message on an unknown `test_id` or `module`, but FastMCP 2.14.7 rewrites any exception from a prompt function into a generic `Error rendering prompt <name>.` before it reaches the client — see `fastmcp/prompts/prompt.py:381`. The specific message is still written to stderr. Tool and resource errors are not affected; those surface verbatim.
