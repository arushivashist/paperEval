#!/usr/bin/env python3
"""
Collect run_meta.json + verdict.json across work/ into results/results.json, and inject it into
dashboard/index.html so the dashboard is a single self-contained file you can open or publish.

    python scorer/score.py
"""
import datetime, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK, TASKS, OUT = ROOT / "work", ROOT / "tasks", ROOT / "results"
DASH = ROOT / "dashboard" / "index.html"
HIGHLIGHTS = ROOT / "dashboard" / "highlights.json"


def git_commit() -> str:
    """N1: the scaffold commit hash, stamped into results.json and the dashboard footer."""
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True, timeout=10)
        if h.returncode == 0:
            dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                   capture_output=True, text=True, timeout=10)
            return h.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "")
    except Exception:  # noqa: BLE001
        pass
    return "no-git"


def inject(html: str, tag_id: str, obj) -> str:
    pat = rf"(<script id=\"{tag_id}\" type=\"application/json\">).*?(</script>)"
    return re.sub(pat, lambda m: m.group(1) + json.dumps(obj) + m.group(2), html, flags=re.S)


def main():
    OUT.mkdir(exist_ok=True)
    tasks = {d.name: json.loads((d / "task.json").read_text()) for d in sorted(TASKS.iterdir()) if (d / "task.json").exists()}
    models, cells = [], []
    for mdir in sorted(WORK.iterdir()) if WORK.exists() else []:
        if not mdir.is_dir():
            continue
        models.append(mdir.name)
        for tdir in sorted(mdir.iterdir()):
            meta = json.loads((tdir / "run_meta.json").read_text()) if (tdir / "run_meta.json").exists() else {}
            verd = json.loads((tdir / "verdict.json").read_text()) if (tdir / "verdict.json").exists() else {}
            rep = json.loads((tdir / "report.json").read_text()) if (tdir / "report.json").exists() else {}
            cells.append({
                "model": mdir.name, "task": tdir.name,
                "tier": tasks.get(tdir.name, {}).get("tier"),
                "outcome": verd.get("outcome", "not_run" if not meta else "ungraded"),
                "fidelity": verd.get("fidelity"),
                "agent_verdict": rep.get("verdict"),
                "cost_usd": meta.get("cost_usd"), "wall_s": meta.get("duration_s") or meta.get("wall_s"),
                "turns": meta.get("num_turns"), "reason": verd.get("outcome_reason"),
            })
    summary = {}
    for m in models:
        mc = [c for c in cells if c["model"] == m]
        summary[m] = {
            "pass": sum(c["outcome"] == "pass" for c in mc),
            "partial": sum(c["outcome"] == "partial" for c in mc),
            "fail": sum(c["outcome"] in ("fail",) for c in mc),
            "total": len(mc),
            "cost_usd": round(sum(c["cost_usd"] or 0 for c in mc), 2),
            "wall_min": round(sum(c["wall_s"] or 0 for c in mc) / 60, 1),
        }
    results = {"models": models, "tasks": [{"id": k, "tier": v.get("tier"), "title": v.get("title") or v.get("claim", {}).get("hypothesis", "")[:90]} for k, v in tasks.items()],
               "cells": cells, "summary": summary,
               "commit": git_commit(),
               "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    (OUT / "results.json").write_text(json.dumps(results, indent=2))
    highlights = json.loads(HIGHLIGHTS.read_text()) if HIGHLIGHTS.exists() else []
    html = inject(DASH.read_text(), "data", results)
    html = inject(html, "highlights", highlights)
    DASH.write_text(html)
    print(json.dumps(summary, indent=2))
    print(f"commit {results['commit']}; wrote {OUT/'results.json'} and refreshed {DASH}")


if __name__ == "__main__":
    main()
