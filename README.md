## What 

Can a Claude Code agent replicate published research on its own, and how much better is Fable 5.1 at it than Opus 5? Full spec: `PRD.md`.

Same frozen scaffold, two models, seven replication tasks (Tier A: run the authors' code · Tier B: paper + new data · Tier C: paper only). An independent, fixed grader (`claude-sonnet-5`) scores every attempt; the dashboard is one self-contained HTML file.

## The three commands

**Friday evening** — fetch, baseline run, verify, score, go/no-go:
```bash
scripts/friday.sh claude-opus-5
```

**Saturday 9:15** — new-model column, verify both, score:
```bash
scripts/saturday.sh claude-fable-5-1
```

**Look at the results** (rerun `scorer/score.py` any time to refresh):
```bash
open dashboard/index.html
```

## Rerunning a single failed task

```bash
python3 runner/run.py --tasks B1_covid_mobility --models claude-fable-5-1
python3 verifier/verify.py --models claude-fable-5-1 --tasks B1_covid_mobility
python3 scorer/score.py
```
A rerun replaces `work/<model>/<task>/` but keeps the old metadata as `run_meta.prev.json`. Add `--dry-run` to `runner/run.py` to print the commands without spending credits.

## Before Friday's run (once)

1. Read `tasks/B*/ground_truth/human_report.*` and fill `human_verdict` in each `tasks/B*/task.json` (`replicated | not_replicated | mixed`). At least one should be `not_replicated`.
2. Commit, so the scorer can stamp the commit hash into `results.json` and the dashboard footer. Freeze the scaffold with `git tag baseline` after a green Friday run.

## During Saturday

- Gotcha panel: paste two short transcript excerpts from `work/<model>/<task>/` into `dashboard/highlights.json`, then `python3 scorer/score.py`.
- Backup video: follow `scripts/record_backup.md` (done by 15:00).
- Cost: each run's `cost_usd` is in `work/<model>/<task>/run_meta.json`; runs over $8 are flagged `over_budget`.

## Layout

```
tasks/<id>/           task.json, prompt.md, (fetch.sh | data + paper), ground_truth/ (B only — never copied to work/)
runner/run.py         run each (model, task) via headless Claude Code
verifier/verify.py    independent grader; writes verdict.json per run
scorer/score.py       aggregates to results/results.json, injects into the dashboard
dashboard/index.html  self-contained scorecard (sample data until first real score)
work/<model>/<task>/  agent output: report.json, run_meta.json, verdict.json
```

Requirements: Claude Code installed and logged in (or `ANTHROPIC_API_KEY`); Python 3.11+, stdlib only. Do not edit `tasks/*/prompt.md` — the prompts are part of the frozen scaffold.
