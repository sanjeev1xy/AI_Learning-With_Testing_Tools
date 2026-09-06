"""DeepEval Framework dashboard — Subsystem C.  Port 8203.

    uvicorn dashboard.app:app --port 8203     # from 03_DeepFramework/

One card per metric. Each card runs on demand against the selected target
(chatbot :8201 or RAG :8202), scored by the judge LLM. Results persist to
dashboard/results.json.

    GET  /                     the dashboard
    GET  /api/status           targets up? + every metric's latest run
    POST /api/run/{key}        run one metric  (json: target, limit)
    POST /api/run-all          run many        (json: keys[], target, limit)
    GET  /health
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT / ".env", ROOT / ".env.local"):
    if _p.exists():
        load_dotenv(_p)
_key = os.getenv("GROQ_API_KEY") or os.getenv("LOCAL_MODEL_API_KEY")
if _key:
    os.environ.setdefault("GROQ_API_KEY", _key)
    os.environ["OPENAI_API_KEY"] = _key

from dashboard.runner import run_batch_bg, run_metric_bg, state  # noqa: E402
from metrics_catalog import ALL_SPECS, CATEGORIES  # noqa: E402
from targets import ChatbotTarget, RagTarget  # noqa: E402

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
app = FastAPI(title="DeepEval Framework Dashboard", version="2.0.0")

JUDGE = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")
CHATBOT_URL = os.getenv("CHATBOT_URL", "http://localhost:8201")
RAG_URL = os.getenv("RAG_URL", "http://localhost:8202")


def _specs_payload() -> list[dict]:
    return [s.as_dict() for s in ALL_SPECS]


def _status_payload() -> dict:
    st = state()
    runs = st["runs"]
    counts = {"pass": 0, "fail": 0, "error": 0, "pending": 0}
    for s in ALL_SPECS:
        # latest run for this metric on any target
        rec = None
        for t in s.targets:
            rec = runs.get(f"{t}:{s.key}") or rec
        v = (rec or {}).get("verdict")
        if v == "pass":
            counts["pass"] += 1
        elif v == "fail":
            counts["fail"] += 1
        elif v == "error" or (rec or {}).get("status") == "error":
            counts["error"] += 1
        else:
            counts["pending"] += 1
    return {
        "chatbot_up": ChatbotTarget().is_up(),
        "rag_up": RagTarget().is_up(),
        "chatbot_url": CHATBOT_URL,
        "rag_url": RAG_URL,
        "judge": JUDGE,
        "counts": counts,
        "runs": runs,
        "running": st["running"],
        "batch": st["batch"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "judge": JUDGE, **_status_payload()["counts"]}


@app.get("/api/status")
def api_status():
    return JSONResponse(_status_payload())


@app.get("/api/specs")
def api_specs():
    return JSONResponse(_specs_payload())


@app.post("/api/run/{key}")
def api_run(key: str, body: dict = Body(default={})):
    target = body.get("target", "chatbot")
    limit = int(body.get("limit", 1))
    run_metric_bg(key, target=target, limit=limit)
    return JSONResponse({"started": key, "target": target, "limit": limit})


@app.post("/api/run-all")
def api_run_all(body: dict = Body(default={})):
    keys = body.get("keys") or [s.key for s in ALL_SPECS]
    target = body.get("target", "chatbot")
    limit = int(body.get("limit", 1))
    run_batch_bg(keys, target=target, limit=limit)
    return JSONResponse({"started": len(keys), "target": target, "limit": limit})


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "specs": _specs_payload(),
            "categories": CATEGORIES,
            "status": _status_payload(),
            "judge": JUDGE,
        },
    )
