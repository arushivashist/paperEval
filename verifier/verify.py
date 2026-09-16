#!/usr/bin/env python3
"""
Independent verifier. For each work/<model>/<task>/report.json it asks a *separate* Claude session
(default: claude-sonnet-5, fixed across all runs so grading is not confounded with the model under test)
two questions:
  1. Fidelity: did the agent compute the thing the paper actually claims, or a proxy?
  2. Match: is the reported number within tolerance of ground truth (Tier A) / consistent with the
     human replication verdict (Tier B, C)?

Numeric matching for Tier A is done in plain Python first; the model only adjudicates fidelity and
free-text cases. Output: work/<model>/<task>/verdict.json

    python verifier/verify.py --models claude-opus-5 claude-fable-5-1
"""
import argparse, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS, WORK = ROOT / "tasks", ROOT / "work"

VERIFIER_PROMPT = """You are an independent verifier for a research-replication benchmark. You did not perform the replication and must not trust the agent's self-assessment.

You will receive:
- TASK: the claim/questions the agent was asked to reproduce and the ground truth.
- REPORT: the agent's report.json.
- AGENT FILES: names of files the agent produced (you may open them with your tools if needed; the paper PDF is in the same directory).

Answer strictly as JSON:
{
  "fidelity": "correct_method" | "proxy_or_wrong_method" | "unclear",
  "fidelity_reason": "<1-2 sentences>",
  "outcome": "pass" | "fail" | "partial",
  "outcome_reason": "<1-2 sentences; cite specific numbers>",
  "hallucination_risk": "low" | "medium" | "high",
  "notes": "<optional>"
}

Definitions:
- Tier A (reproduce with code): pass = every question answered within tolerance AND the number was observed in an actual output.
- Tier B (replicate with new data): pass = agent's verdict matches HUMAN_VERDICT, using a sound test of the focal claim. If HUMAN_VERDICT is not filled in, judge from the human report if available and say so.
- Tier C: pass = success criteria in TASK are met by the agent's logged metrics.
- 'partial' = right method, number slightly outside tolerance, or 1 of N questions wrong.
Be skeptical of round numbers, numbers that match the paper too exactly with no output file, and reports without code."""


def numeric_check(task: dict, report: dict) -> dict:
    """Tier A: compare answers to gold runs with relative tolerance. Returns per-question results."""
    tol = task.get("tolerance", {}).get("numeric_rel", 0.05)
    out = {}
    answers = report.get("answers", {}) or {}
    for q, g in task.get("questions", {}).items():
        gold = g["gold_runs"]
        ans = answers.get(q)
        if ans is None:
            out[q] = {"ok": False, "why": "missing"}
            continue
        try:
            gold_nums = [float(x) for x in gold]
            a = float(str(ans).strip().rstrip("%"))
            lo, hi = min(gold_nums), max(gold_nums)
            span = max(abs(hi - lo), tol * max(abs(lo), abs(hi), 1e-9))
            ok = (lo - span) <= a <= (hi + span)
            out[q] = {"ok": ok, "answer": a, "gold": gold_nums}
        except (TypeError, ValueError):
            ok = str(ans).strip().lower().rstrip(".") == str(gold[0]).strip().lower().rstrip(".")
            out[q] = {"ok": ok, "answer": ans, "gold": gold}
    return out


def verify_one(model: str, task_id: str, grader: str) -> dict:
    wd = WORK / model / task_id
    task = json.loads((TASKS / task_id / "task.json").read_text())
    rep_path = wd / "report.json"
    if not rep_path.exists():
        v = {"outcome": "fail", "fidelity": "unclear", "outcome_reason": "no report.json produced"}
        (wd / "verdict.json").write_text(json.dumps(v, indent=2))
        return v
    report = json.loads(rep_path.read_text())

    pre = {}
    if task["tier"] == "A":
        pre["numeric_check"] = numeric_check(task, report)

    gt_dir = TASKS / task_id / "ground_truth"
    human_verdict = task.get("human_verdict", "n/a")
    files = sorted(p.name for p in wd.iterdir() if p.is_file() and p.name not in ("run_meta.json",))
    payload = (
        f"TASK:\n{json.dumps(task, indent=1)[:6000]}\n\nHUMAN_VERDICT: {human_verdict}\n"
        f"GROUND_TRUTH_DIR: {gt_dir if gt_dir.exists() else 'none'}\n\n"
        f"PRECOMPUTED_CHECKS:\n{json.dumps(pre, indent=1)[:3000]}\n\n"
        f"REPORT:\n{json.dumps(report, indent=1)[:6000]}\n\nAGENT FILES: {files}"
    )
    cmd = ["claude", "-p", VERIFIER_PROMPT + "\n\n" + payload, "--model", grader,
           "--output-format", "json", "--max-turns", "12", "--permission-mode", "bypassPermissions"]
    # V6: malformed grader output gets one retry, then a clean fail verdict instead of crashing the batch
    v = None
    for attempt in (1, 2):
        try:
            p = subprocess.run(cmd, cwd=wd, capture_output=True, text=True, timeout=900)
            text = json.loads(p.stdout).get("result", "")
            m = re.search(r"\{.*\}", text, re.S)
            if not m:
                raise ValueError(f"no JSON in grader output: {text[:300]!r}")
            v = json.loads(m.group(0))
            v["verifier_attempts"] = attempt
            break
        except Exception as e:  # noqa: BLE001 — any grader failure is retried once, then recorded
            err = f"{type(e).__name__}: {e}"
            if attempt == 2:
                v = {"outcome": "fail", "fidelity": "unclear",
                     "outcome_reason": "verifier error", "verifier_error": err[:500],
                     "verifier_attempts": attempt}
    v["precomputed"] = pre
    v["grader_model"] = grader
    (wd / "verdict.json").write_text(json.dumps(v, indent=2))
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--tasks", nargs="*")
    ap.add_argument("--grader", default="claude-sonnet-5", help="keep FIXED across all runs")
    a = ap.parse_args()
    for m in a.models:
        mdir = WORK / m
        if not mdir.exists():
            print(f"[{m}] no work dir, skipping")
            continue
        for d in sorted(mdir.iterdir()):
            if not d.is_dir() or (a.tasks and d.name not in a.tasks):
                continue
            try:
                v = verify_one(m, d.name, a.grader)
            except Exception as e:  # noqa: BLE001 — one bad task must not kill the batch (V6)
                v = {"outcome": "fail", "fidelity": "unclear",
                     "outcome_reason": "verifier error", "verifier_error": str(e)[:500],
                     "grader_model": a.grader}
                (d / "verdict.json").write_text(json.dumps(v, indent=2))
            print(f"[{m}] {d.name}: {v.get('outcome')} / {v.get('fidelity')} - {v.get('outcome_reason','')[:90]}")


if __name__ == "__main__":
    main()
