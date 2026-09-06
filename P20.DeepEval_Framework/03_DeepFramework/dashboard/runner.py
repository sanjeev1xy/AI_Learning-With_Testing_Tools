"""Run the metric catalog directly (no pytest) and keep structured results.

Powers the dashboard: one metric at a time (the card's Run button), or a
batch (Run all visible), against a chosen target (chatbot :8201 or RAG :8202).

Results persist to ``results.json`` keyed by ``"<target>:<metric_key>"`` so the
dashboard survives a restart.
"""
from __future__ import annotations

import json
import os
import threading
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path

from llm_Providers import build_judge
from metrics_catalog import SPEC_REGISTRY, MetricSpec
from targets import ChatbotTarget, RagTarget

RESULTS_PATH = Path(__file__).resolve().parent / "results.json"

CASE_DELAY_S = float(os.getenv("EVAL_CASE_DELAY", "3"))
RATE_LIMIT_BACKOFF_S = float(os.getenv("EVAL_RATE_BACKOFF", "35"))

_LOCK = threading.Lock()
_RUNNING: set[str] = set()          # metric keys currently executing
_RESULTS: dict[str, dict] = {}      # "<target>:<key>" -> result dict
_BATCH = {"active": False, "total": 0, "done": 0, "current": ""}


# --------------------------------------------------------------------------

@dataclass
class CaseResult:
    input: str
    reply: str
    score: float | None
    passed: bool | None
    reason: str
    error: str | None = None


@dataclass
class MetricRun:
    key: str
    title: str
    target: str
    threshold: float
    status: str = "not_run"          # not_run | running | done | error
    passed: int = 0
    failed: int = 0
    errored: int = 0
    avg_score: float | None = None
    verdict: str | None = None       # pass | fail | error
    started_at: float | None = None
    finished_at: float | None = None
    cases: list[CaseResult] = field(default_factory=list)
    error: str | None = None

    def roll_up(self) -> None:
        self.passed = sum(1 for c in self.cases if c.passed and not c.error)
        self.failed = sum(1 for c in self.cases if c.passed is False and not c.error)
        self.errored = sum(1 for c in self.cases if c.error)
        scores = [c.score for c in self.cases if c.score is not None]
        self.avg_score = round(sum(scores) / len(scores), 3) if scores else None
        if self.errored and not self.cases:
            self.verdict = "error"
        elif self.failed:
            self.verdict = "fail"
        elif self.passed:
            self.verdict = "pass"
        else:
            self.verdict = "error" if self.errored else None


def _persist() -> None:
    try:
        RESULTS_PATH.write_text(json.dumps({"runs": _RESULTS}, indent=2), encoding="utf-8")
    except Exception:
        pass


def _load() -> None:
    global _RESULTS
    if RESULTS_PATH.exists():
        try:
            _RESULTS = json.loads(RESULTS_PATH.read_text(encoding="utf-8")).get("runs", {})
        except Exception:
            _RESULTS = {}


_load()


def _is_rate_limit(exc: BaseException) -> bool:
    s = f"{type(exc).__name__} {exc}".lower()
    return "ratelimit" in s or "rate_limit" in s or "429" in s


def _case_prompt(item) -> str:
    if hasattr(item, "prompt"):
        return item.prompt
    if hasattr(item, "input"):
        return item.input
    if hasattr(item, "user_turns"):
        return item.user_turns[0]
    return str(item)


# --------------------------------------------------------------------------

def state() -> dict:
    return {
        "runs": _RESULTS,
        "running": sorted(_RUNNING),
        "batch": dict(_BATCH),
    }


def _get_target(name: str):
    return RagTarget() if name == "rag" else ChatbotTarget()


def _measure_single(spec: MetricSpec, item, out, judge) -> CaseResult:
    inp = _case_prompt(item)
    reply_text = out if isinstance(out, str) else (out[0] if out else "")
    for attempt in (1, 2):
        try:
            tc = spec.build_case(item, out)
            metric = spec.build_metric(judge)
            metric.measure(tc)
            return CaseResult(
                input=inp,
                reply=reply_text if isinstance(reply_text, str) else str(reply_text),
                score=float(metric.score) if metric.score is not None else None,
                passed=bool(metric.is_successful()),
                reason=(metric.reason or "").strip(),
            )
        except Exception as e:  # noqa: BLE001
            if attempt == 1 and _is_rate_limit(e):
                time.sleep(RATE_LIMIT_BACKOFF_S)
                continue
            return CaseResult(inp, reply_text or "", None, None, "", error=f"{type(e).__name__}: {e}")


def _run_conversational(spec: MetricSpec, bot, judge, limit: int) -> MetricRun:
    run = MetricRun(key=spec.key, title=spec.title, target="chatbot", threshold=spec.threshold,
                    status="running", started_at=time.time())
    for g in spec.cases()[: max(1, limit)]:
        try:
            replies = [bot.chat(t).reply for t in g.user_turns]
            tc = spec.build_case(g, replies)
            metric = spec.build_metric(judge)
            metric.measure(tc)
            run.cases.append(CaseResult(
                input=g.user_turns[0] + f"  (+{len(g.user_turns) - 1} turns)",
                reply=" | ".join(r[:80] for r in replies),
                score=float(metric.score) if metric.score is not None else None,
                passed=bool(metric.is_successful()),
                reason=(metric.reason or "").strip(),
            ))
        except Exception as e:  # noqa: BLE001
            run.cases.append(CaseResult(g.name, "", None, None, "", error=f"{type(e).__name__}: {e}"))
        time.sleep(CASE_DELAY_S)
    run.status = "done"
    run.finished_at = time.time()
    run.roll_up()
    return run


def run_metric(key: str, target: str = "chatbot", limit: int = 1) -> dict:
    spec = SPEC_REGISTRY.get(key)
    if not spec:
        return {"error": f"unknown metric {key}"}
    if target not in spec.targets:
        target = spec.targets[0]

    slot = f"{target}:{key}"
    with _LOCK:
        if key in _RUNNING:
            return _RESULTS.get(slot, {"status": "running"})
        _RUNNING.add(key)

    run = MetricRun(key=key, title=spec.title, target=target, threshold=spec.threshold,
                    status="running", started_at=time.time())
    _RESULTS[slot] = asdict(run)
    _persist()

    try:
        tgt = _get_target(target)
        if not tgt.is_up():
            raise RuntimeError(f"{target} target not reachable")
        if target == "rag" and hasattr(tgt, "ensure_corpus"):
            tgt.ensure_corpus()
        judge = build_judge()

        if spec.conversational:
            run = _run_conversational(spec, tgt, judge, limit)
            run.target = target
        else:
            reply_cache: dict[str, object] = {}
            for item in spec.cases()[: max(1, limit)]:
                prompt = _case_prompt(item)
                if prompt not in reply_cache:
                    try:
                        r = tgt.chat(prompt)
                        reply_cache[prompt] = (
                            (r.reply, getattr(r, "retrieval_context", []))
                            if (spec.retrieval or spec.category == "retrieval")
                            else r.reply
                        )
                    except Exception as e:  # noqa: BLE001
                        run.cases.append(CaseResult(prompt, "", None, None, "",
                                                    error=f"target call failed: {e}"))
                        continue
                run.cases.append(_measure_single(spec, item, reply_cache[prompt], judge))
                _RESULTS[slot] = _snapshot(run)
                _persist()
                time.sleep(CASE_DELAY_S)
            run.status = "done"
            run.finished_at = time.time()
            run.roll_up()

        tgt.close()
        _RESULTS[slot] = asdict(run)
    except Exception:  # noqa: BLE001
        run.status = "error"
        run.error = traceback.format_exc()
        run.finished_at = time.time()
        run.roll_up()
        _RESULTS[slot] = asdict(run)
    finally:
        _RUNNING.discard(key)
        _persist()
    return _RESULTS[slot]


def _snapshot(run: MetricRun) -> dict:
    run.roll_up()
    return asdict(run)


def run_metric_bg(key: str, target: str = "chatbot", limit: int = 1) -> None:
    threading.Thread(target=run_metric, kwargs=dict(key=key, target=target, limit=limit),
                     daemon=True).start()


def run_batch_bg(keys: list[str], target: str = "chatbot", limit: int = 1) -> None:
    def _work():
        _BATCH.update(active=True, total=len(keys), done=0, current="")
        for k in keys:
            spec = SPEC_REGISTRY.get(k)
            if not spec:
                _BATCH["done"] += 1
                continue
            t = target if target in spec.targets else spec.targets[0]
            _BATCH["current"] = spec.title
            run_metric(k, target=t, limit=limit)
            _BATCH["done"] += 1
        _BATCH.update(active=False, current="")

    threading.Thread(target=_work, daemon=True).start()


# --------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    from metrics_catalog import ALL_SPECS

    ap = argparse.ArgumentParser(description="Run the DeepEval metric catalog.")
    ap.add_argument("--target", default="chatbot", choices=["chatbot", "rag"])
    ap.add_argument("--category", nargs="*")
    ap.add_argument("--keys", nargs="*")
    ap.add_argument("--limit", type=int, default=1)
    args = ap.parse_args()

    if args.keys:
        keys = args.keys
    elif args.category:
        keys = [s.key for s in ALL_SPECS if s.category in args.category and args.target in s.targets]
    else:
        keys = [s.key for s in ALL_SPECS if args.target in s.targets]

    for k in keys:
        res = run_metric(k, target=args.target, limit=args.limit)
        v = res.get("verdict") or res.get("status")
        print(f"{v:6} {k:24} avg={res.get('avg_score')}  "
              f"(p{res.get('passed')} f{res.get('failed')} e{res.get('errored')})")
