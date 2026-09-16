#!/usr/bin/env python3
"""
Run every task against every model with an identical scaffold (Claude Code, headless).

    python runner/run.py --models claude-opus-5 claude-fable-5-1 --tasks A1_hyperETA B1_covid_mobility
    python runner/run.py --all --models claude-fable-5-1 --parallel 4

For each (model, task) it:
  1. copies tasks/<task>/ into work/<model>/<task>/ (minus ground_truth/, which the agent must never see)
  2. runs `claude -p <prompt> --model <model> --output-format json --max-turns N` in that directory
  3. saves claude's JSON envelope (cost, duration, turns) to work/<model>/<task>/run_meta.json

Requires Claude Code installed and logged in (`claude --version`), and ANTHROPIC_API_KEY or console login.
"""
import argparse, json, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
WORK = ROOT / "work"

SYSTEM_SUFFIX = (
    "You are an autonomous research-replication agent. Work only inside the current directory. "
    "Never fabricate numbers; every reported value must come from an output you produced. "
    "Finish by writing report.json exactly as specified, then stop."
)


def stage(task: str, model: str) -> Path:
    src = TASKS / task
    dst = WORK / model / task
    prev_meta = None  # R5: keep the previous run's metadata across a rerun
    if dst.exists():
        for name in ("run_meta.json", "run_meta.prev.json"):
            p = dst / name
            if p.exists():
                prev_meta = p.read_text()
                break
        shutil.rmtree(dst)
    # task.json holds gold_runs / human_verdict, and the *_results/post_registration files are
    # prior replication attempts with outcomes — all of it is ground truth the agent must not see (R1)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        "ground_truth", "fetch.sh", "*.pyc", "task.json",
        "post_registration.json", "interpret_results.json", "execution_results.json",
        "_log", "_runtime"))
    if (src / "capsule").exists() and not (dst / "capsule").exists():
        shutil.copytree(src / "capsule", dst / "capsule")
    if prev_meta is not None:
        (dst / "run_meta.prev.json").write_text(prev_meta)
    return dst


def build_cmd(model: str, max_turns: int) -> list:
    return [
        "claude", "-p", "<PROMPT>",
        "--model", model,
        "--output-format", "json",
        "--max-turns", str(max_turns),
        "--append-system-prompt", SYSTEM_SUFFIX,
        "--permission-mode", "bypassPermissions",
    ]


def run_one(task: str, model: str, max_turns: int, max_budget: float, timeout: int) -> dict:
    wd = stage(task, model)
    prompt = (wd / "prompt.md").read_text()
    cmd = build_cmd(model, max_turns)
    cmd[2] = prompt
    t0 = time.time()
    meta = {"task": task, "model": model, "started": t0, "timed_out": False,
            "cmd": " ".join(cmd[:2] + ["<prompt.md>"] + cmd[3:])}
    try:
        p = subprocess.run(cmd, cwd=wd, capture_output=True, text=True, timeout=timeout)
        meta["returncode"] = p.returncode
        meta["stderr_tail"] = p.stderr[-2000:]
        try:
            env = json.loads(p.stdout)
            meta.update({
                "cost_usd": env.get("total_cost_usd"),
                "duration_s": (env.get("duration_ms") or 0) / 1000,
                "num_turns": env.get("num_turns"),
                "session_id": env.get("session_id"),
                "is_error": env.get("is_error"),
                "final_text": (env.get("result") or "")[-3000:],
            })
        except json.JSONDecodeError:
            meta["raw_stdout_tail"] = p.stdout[-3000:]
    except subprocess.TimeoutExpired:
        meta["returncode"] = -1
        meta["timed_out"] = True
    meta["wall_s"] = round(time.time() - t0, 1)
    meta["report_exists"] = (wd / "report.json").exists()
    if max_budget and meta.get("cost_usd") and meta["cost_usd"] > max_budget:
        meta["over_budget"] = True
    (wd / "run_meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--tasks", nargs="*", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--max-budget", type=float, default=8.0, help="USD; flag only, does not stop the run")
    ap.add_argument("--timeout", type=int, default=2400, help="seconds per run")
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true", help="print the exact commands without executing")
    a = ap.parse_args()

    tasks = a.tasks or ([d.name for d in sorted(TASKS.iterdir()) if d.is_dir()] if a.all else [])
    if not tasks:
        sys.exit("give --tasks or --all")
    for t in tasks:
        if t.startswith("A") and not (TASKS / t / "capsule").exists():
            sys.exit(f"{t}: run tasks/{t}/fetch.sh first")

    jobs = [(t, m) for m in a.models for t in tasks]
    if a.dry_run:
        for t, m in jobs:
            cmd = build_cmd(m, a.max_turns)
            cmd[2] = f"$(cat {TASKS / t / 'prompt.md'})"
            print(f"# cwd={WORK / m / t}  (staged from tasks/{t}, minus ground_truth/)")
            print("  " + " ".join(cmd))
        print(f"# {len(jobs)} runs, {a.parallel} in parallel, timeout {a.timeout}s each — nothing executed")
        return
    print(f"{len(jobs)} runs, {a.parallel} in parallel")
    with ThreadPoolExecutor(a.parallel) as ex:
        futs = {ex.submit(run_one, t, m, a.max_turns, a.max_budget, a.timeout): (t, m) for t, m in jobs}
        for f in as_completed(futs):
            m = f.result()
            print(f"[{m['model']}] {m['task']}: report={m['report_exists']} "
                  f"cost=${m.get('cost_usd')} turns={m.get('num_turns')} wall={m['wall_s']}s")


if __name__ == "__main__":
    main()
