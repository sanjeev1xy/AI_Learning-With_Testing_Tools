"""Generate docs/deepeval_framework_workflow.excalidraw — an Excalidraw scene
of how one metric evaluation flows through the framework.

    python docs/build_excalidraw.py
    # then open the .excalidraw file at https://excalidraw.com

Kept as a script so the diagram stays in sync when the pipeline changes.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "deepeval_framework_workflow.excalidraw"

INK = "#1e1e1e"
ACCENT = "#e8590c"      # the judge loop
MUTED = "#495057"


def _seed() -> int:
    return random.randint(1, 2**31)


_elements: list[dict] = []


def box(bid, x, y, w, h, title, lines, stroke=INK):
    _elements.append({
        "id": bid, "type": "rectangle", "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": stroke, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 3}, "seed": _seed(), "version": 1, "versionNonce": _seed(),
        "isDeleted": False, "boundElements": [], "updated": 1, "link": None, "locked": False,
    })
    label = title if not lines else title + "\n" + "\n".join(lines)
    _elements.append({
        "id": bid + "_t", "type": "text", "x": x + 10, "y": y + 10,
        "width": w - 20, "height": h - 20, "angle": 0, "strokeColor": stroke,
        "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 2,
        "strokeStyle": "solid", "roughness": 1, "opacity": 100, "groupIds": [],
        "frameId": None, "roundness": None, "seed": _seed(), "version": 1,
        "versionNonce": _seed(), "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "text": label, "fontSize": 16, "fontFamily": 1, "textAlign": "center",
        "verticalAlign": "middle", "containerId": bid, "originalText": label,
        "lineHeight": 1.25,
    })


def arrow(x1, y1, x2, y2, label="", color=INK, dashed=False):
    aid = f"a{_seed()}"
    _elements.append({
        "id": aid, "type": "arrow", "x": x1, "y": y1,
        "width": abs(x2 - x1), "height": abs(y2 - y1), "angle": 0,
        "strokeColor": color, "backgroundColor": "transparent", "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "dashed" if dashed else "solid",
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 2}, "seed": _seed(), "version": 1, "versionNonce": _seed(),
        "isDeleted": False, "boundElements": [], "updated": 1, "link": None, "locked": False,
        "points": [[0, 0], [x2 - x1, y2 - y1]], "lastCommittedPoint": None,
        "startBinding": None, "endBinding": None,
        "startArrowhead": None, "endArrowhead": "arrow",
    })
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 10
        _elements.append({
            "id": aid + "_l", "type": "text", "x": mx - 60, "y": my,
            "width": 120, "height": 18, "angle": 0, "strokeColor": color,
            "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 2,
            "strokeStyle": "solid", "roughness": 1, "opacity": 100, "groupIds": [],
            "frameId": None, "roundness": None, "seed": _seed(), "version": 1,
            "versionNonce": _seed(), "isDeleted": False, "boundElements": [],
            "updated": 1, "link": None, "locked": False,
            "text": label, "fontSize": 12, "fontFamily": 1, "textAlign": "center",
            "verticalAlign": "top", "containerId": None, "originalText": label,
            "lineHeight": 1.25,
        })


def heading(x, y, text, color=MUTED, size=13):
    _elements.append({
        "id": f"h{_seed()}", "type": "text", "x": x, "y": y, "width": 600, "height": 20,
        "angle": 0, "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1,
        "opacity": 100, "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(), "version": 1, "versionNonce": _seed(), "isDeleted": False,
        "boundElements": [], "updated": 1, "link": None, "locked": False,
        "text": text, "fontSize": size, "fontFamily": 1, "textAlign": "left",
        "verticalAlign": "top", "containerId": None, "originalText": text,
        "lineHeight": 1.25,
    })


# ---- scene -------------------------------------------------------------------

heading(40, 20, "DeepEval Framework — one metric evaluation", INK, 20)
heading(40, 50, "Subsystem C scores Subsystem A (chatbot) and Subsystem B (RAG) with a separate judge LLM.")

box("datasets", 40, 110, 200, 90, "datasets/",
    ["goldens · attacks", "conversations"])
box("spec", 40, 250, 200, 90, "MetricSpec  (x25)",
    [".cases() .build_case()", ".build_metric()"])
box("target", 320, 180, 230, 110, "target LLM",
    ["ChatbotTarget  :8201", "RagTarget      :8202", "qwen/qwen3.8-27b  (Groq)"])
box("tc", 320, 360, 230, 100, "LLMTestCase",
    ["input · actual_output", "expected · retrieval_context"])
box("judge", 630, 360, 230, 100, "judge LLM   metric.measure()",
    ["openai/gpt-oss-120b  (Groq)", "rubric / reference scoring"], stroke=ACCENT)
box("verdict", 630, 180, 230, 110, "score  vs  threshold",
    ["0.0 - 1.0   +   reason", "PASS / FAIL"])
box("dash", 950, 110, 190, 80, "dashboard  :8203", ["one card per metric"])
box("pytest", 950, 250, 190, 80, "pytest", ["assert_test · 263 cases"])

arrow(140, 200, 140, 248, "")                                  # datasets -> spec
arrow(240, 235, 318, 235, "prompt")                            # spec -> target
arrow(435, 290, 435, 358, "reply (+ chunks)")                  # target -> tc
arrow(240, 320, 318, 400, "case shape")                        # spec -> tc
arrow(550, 410, 628, 410, "test case", ACCENT)                # tc -> judge
arrow(745, 358, 745, 292, "score", ACCENT)                    # judge -> verdict
arrow(860, 210, 948, 150, "")                                  # verdict -> dashboard
arrow(860, 245, 948, 280, "")                                  # verdict -> pytest
arrow(1045, 190, 1045, 240, "", MUTED, dashed=True)
arrow(1045, 330, 1045, 470, "", MUTED, dashed=True)
arrow(1045, 470, 140, 470, "", MUTED, dashed=True)
arrow(140, 470, 140, 342, "both entry points → same catalog", MUTED, dashed=True)

heading(40, 520, "Solid = data flow.   Orange = the judge loop (a second, different LLM).   Dashed = shared control path.")
heading(40, 545, "retrieval_context is only filled by RagTarget — that is what the 3 retrieval metrics score.")

scene = {
    "type": "excalidraw",
    "version": 2,
    "source": "P20.DeepEval_Framework/03_DeepFramework/docs/build_excalidraw.py",
    "elements": _elements,
    "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
    "files": {},
}

OUT.write_text(json.dumps(scene, indent=2), encoding="utf-8")
print(f"wrote {OUT}  ({len(_elements)} elements)")
