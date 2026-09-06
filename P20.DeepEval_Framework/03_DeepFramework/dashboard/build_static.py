"""Bake a read-only snapshot of the dashboard into dashboard-static/.

The live dashboard needs the chatbot (:8201), the RAG Explorer (:8202), a Groq
key and long-running threads — none of which survive a static host. This emits
a self-contained page: the 25 metric cards + whatever is in results.json,
with the Run / Refresh / Run-all controls removed. Category tabs and the
target filter still work (pure client-side).

    python -m dashboard.build_static
    cd dashboard-static && vercel deploy
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from metrics_catalog import ALL_SPECS, CATEGORIES

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboard-static"
RESULTS = Path(__file__).resolve().parent / "results.json"
JUDGE = "openai/gpt-oss-120b"


def _load_runs() -> dict:
    if RESULTS.exists():
        try:
            return json.loads(RESULTS.read_text(encoding="utf-8")).get("runs", {})
        except Exception:
            return {}
    return {}


def _latest(runs: dict, spec) -> dict | None:
    rec = None
    for t in spec.targets:
        rec = runs.get(f"{t}:{spec.key}") or rec
    return rec


def _esc(s) -> str:
    return html.escape(str(s), quote=True)


def _verdict_html(rec: dict | None) -> str:
    if not rec:
        return '<span class="verdict">not run</span>'
    v = rec.get("verdict")
    if rec.get("status") == "error" and not v:
        v = "error"
    cls = v or ""
    label = v or "not run"
    score = rec.get("avg_score")
    score_s = f'<span class="score">{score:.2f}</span>' if isinstance(score, (int, float)) else ""
    tallies = ""
    if rec:
        tallies = (f'<div class="avail">{rec.get("passed",0)} pass · '
                   f'{rec.get("failed",0)} fail · {rec.get("errored",0)} err</div>')
    return f'<span class="verdict {cls}">{label}</span>{score_s}{tallies}'


def _cases_html(rec: dict | None) -> str:
    if not rec or not rec.get("cases"):
        return ""
    rows = []
    for c in rec["cases"]:
        k = "error" if c.get("error") else ("pass" if c.get("passed") else "fail")
        sc = f' · <b>{c["score"]:.2f}</b>' if isinstance(c.get("score"), (int, float)) else ""
        why = c.get("error") or c.get("reason") or ""
        rows.append(
            f'<div class="caserow {k}"><div class="q">{_esc(c.get("input",""))}{sc}</div>'
            + (f'<div class="r">{_esc(c.get("reply","")[:240])}</div>' if c.get("reply") else "")
            + (f'<div class="why">{_esc(why[:280])}</div>' if why else "")
            + "</div>"
        )
    return f'<details class="details"><summary>Details</summary>{"".join(rows)}</details>'


def build() -> Path:
    runs = _load_runs()
    OUT.mkdir(exist_ok=True)

    counts = {"pass": 0, "fail": 0, "pending": 0, "error": 0}
    for s in ALL_SPECS:
        v = (_latest(runs, s) or {}).get("verdict")
        counts["pass" if v == "pass" else "fail" if v == "fail"
               else "error" if v == "error" else "pending"] += 1

    cards = []
    for s in ALL_SPECS:
        rec = _latest(runs, s)
        chips = f'<span class="chip cat-{s.category}">{s.category}</span>' + "".join(
            f'<span class="chip tgt">{t}</span>' for t in s.targets
        )
        cards.append(f"""
      <div class="mcard" data-cat="{s.category}" data-targets="{','.join(s.targets)}">
        <div class="chips">{chips}<span class="thr">&ge; {s.threshold:.2f}</span></div>
        <h3>{_esc(s.title)}</h3>
        <div class="desc">{_esc(s.blurb)}</div>
        <div class="box">
          <div class="verline">{_verdict_html(rec)}</div>
          <div class="sample">{_esc(s.sample_input())}</div>
          <div class="avail">{s.case_count()} cases · {_esc(s.test_file)}</div>
        </div>
        {_cases_html(rec)}
      </div>""")

    tabs = '<span class="tab on" data-cat="all">all</span>' + "".join(
        f'<span class="tab" data-cat="{c}">{c}</span>' for c in CATEGORIES
    )
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ran = sum(1 for s in ALL_SPECS if _latest(runs, s))

    page = _TEMPLATE.format(
        tabs=tabs, cards="".join(cards), judge=JUDGE, stamp=stamp,
        ran=ran, total=len(ALL_SPECS),
        cpass=counts["pass"], cfail=counts["fail"],
        cpend=counts["pending"] + counts["error"],
    )
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / "vercel.json").write_text(
        json.dumps({"cleanUrls": True, "trailingSlash": False}, indent=2), encoding="utf-8"
    )
    print(f"wrote {OUT/'index.html'}  ({ran}/{len(ALL_SPECS)} metrics have a recorded run)")
    return OUT / "index.html"


_TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DeepEval Dashboard — snapshot</title>
<style>
  :root{{--bg:#f4f3ef;--panel:#fbfaf8;--card:#fff;--ink:#20242c;--muted:#6d7480;
    --line:#e7e4dd;--accent:#d05a33;--pass:#1c8a4e;--pass-bg:#e4f4ec;--fail:#c0392b;
    --fail-bg:#fbe9e7;--pend:#9aa0a6;--pend-bg:#eceae5;--head:#22252c}}
  @media (prefers-color-scheme:dark){{:root{{--bg:#181a1f;--panel:#1f2228;--card:#22262d;
    --ink:#e9e9ec;--muted:#9aa0aa;--line:#33373f;--pass-bg:#12331f;--fail-bg:#3a1c17;
    --pend-bg:#2a2d33;--head:#14161a}}}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);
    font:14px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
  header{{background:var(--head);color:#f4f3ef;padding:16px 22px;display:flex;
    align-items:center;gap:14px;flex-wrap:wrap}}
  header .logo{{width:30px;height:30px;border-radius:8px;background:var(--accent);
    display:flex;align-items:center;justify-content:center;transform:rotate(45deg)}}
  header .logo i{{width:11px;height:11px;background:#fff;border-radius:2px}}
  header h1{{font-size:17px;margin:0}} header .tag{{font-size:12px;color:#b9bcc4}}
  header .snap{{margin-left:auto;font-size:11px;color:#b9bcc4;text-align:right}}
  header a{{color:#f0c3b2}}
  main{{max-width:1180px;margin:0 auto;padding:18px 22px 60px}}
  .statusbar{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px;align-items:center}}
  .note{{background:var(--panel);border:1px solid var(--line);border-radius:9px;
    padding:9px 13px;font-size:12.5px;color:var(--muted);flex:1;min-width:240px}}
  .pill{{padding:3px 10px;border-radius:999px;font-size:13px;font-weight:600}}
  .pill.p{{background:var(--pass-bg);color:var(--pass)}}
  .pill.f{{background:var(--fail-bg);color:var(--fail)}}
  .pill.n{{background:var(--pend-bg);color:#8b9099}}
  .tabs{{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 16px}}
  .tab{{background:var(--panel);border:1px solid var(--line);border-radius:999px;
    padding:5px 13px;font-size:12px;cursor:pointer;text-transform:capitalize}}
  .tab.on{{background:var(--head);color:#f4f3ef;border-color:var(--head)}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}}
  .mcard{{background:var(--card);border:1px solid var(--line);border-radius:12px;
    padding:14px 15px;display:flex;flex-direction:column;gap:8px}}
  .chips{{display:flex;gap:6px;align-items:center;flex-wrap:wrap}}
  .chip{{font-size:9.5px;letter-spacing:.06em;text-transform:uppercase;padding:2px 7px;
    border-radius:5px;background:var(--pend-bg);color:var(--muted);font-weight:700}}
  .chip.cat-quality{{background:#e5eef8;color:#2f6bb0}}
  .chip.cat-retrieval{{background:#e7f1ec;color:#2f855a}}
  .chip.cat-safety{{background:#fdeee6;color:#c0632b}}
  .chip.cat-geval{{background:#f0e9f6;color:#7a4bb0}}
  .chip.cat-conversational{{background:#e9eef0;color:#4a6b78}}
  .thr{{margin-left:auto;font-size:11px;color:var(--muted)}}
  .mcard h3{{margin:0;font-size:15px}}
  .desc{{font-size:12.5px;color:var(--muted);min-height:32px}}
  .box{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:9px 11px;font-size:12px}}
  .verline{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
  .verdict{{font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
    padding:2px 7px;border-radius:5px;background:var(--pend-bg);color:var(--muted)}}
  .verdict.pass{{background:var(--pass-bg);color:var(--pass)}}
  .verdict.fail{{background:var(--fail-bg);color:var(--fail)}}
  .verdict.error{{background:#f7efd9;color:#8a6d1d}}
  .score{{font-weight:700}}
  .sample{{color:var(--muted);font-style:italic;margin-top:5px}}
  .avail{{font-size:11px;color:var(--muted);font-family:ui-monospace,Menlo,monospace;word-break:break-all;margin-top:3px}}
  .details{{border-top:1px dashed var(--line);padding-top:6px}}
  .details summary{{cursor:pointer;font-size:12px;color:var(--accent);font-weight:600}}
  .caserow{{font-size:11.5px;border-left:3px solid var(--line);padding:3px 0 3px 8px;margin-top:6px}}
  .caserow.pass{{border-color:var(--pass)}} .caserow.fail{{border-color:var(--fail)}}
  .caserow.error{{border-color:#c9a227}}
  .caserow .q{{font-weight:600}} .caserow .r{{color:var(--muted);white-space:pre-wrap}}
  .caserow .why{{color:var(--muted);margin-top:2px}}
  footer{{max-width:1180px;margin:0 auto;padding:0 22px 40px;color:var(--muted);font-size:12px;text-align:center}}
</style></head><body>
<header>
  <div class="logo"><i></i></div>
  <div><h1>DeepEval Dashboard</h1>
    <div class="tag">Live metric runs against the chatbot and RAG pipeline — static snapshot</div></div>
  <div class="snap">snapshot {stamp}<br>{ran}/{total} metrics have a recorded run ·
    <a href="./how-it-works.html">how it works</a></div>
</header>
<main>
  <div class="statusbar">
    <div class="note">Read-only snapshot. The interactive dashboard runs locally
      (<code>uvicorn dashboard.app:app --port 8203</code>) against the chatbot on
      :8201 and the RAG Explorer on :8202, scored by the Groq judge
      <code>{judge}</code>.</div>
    <span class="pill p">{cpass} pass</span>
    <span class="pill f">{cfail} fail</span>
    <span class="pill n">{cpend} pending</span>
  </div>
  <div class="tabs" id="tabs">{tabs}</div>
  <div class="grid" id="grid">{cards}</div>
</main>
<footer>DeepEval 4.2.1 · one card per metric · judge ≠ target on purpose ·
  P20.DeepEval_Framework / 03_DeepFramework</footer>
<script>
  document.getElementById('tabs').addEventListener('click', e => {{
    if (!e.target.matches('.tab')) return;
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('on', t === e.target));
    const cat = e.target.dataset.cat;
    document.querySelectorAll('.mcard').forEach(c =>
      c.style.display = (cat === 'all' || c.dataset.cat === cat) ? '' : 'none');
  }});
</script>
</body></html>"""


if __name__ == "__main__":
    build()
