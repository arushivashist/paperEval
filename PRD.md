# PRD: ReplicaBench — Can Claude replicate published science on its own, and how much better is Fable 5.1 at it?

Owner: (you) · Event: Claude Community Build Day, San Francisco, Sat Sep 19 2026, 9:00–16:00 PDT · Track: Breakthrough
Status: prep Fri Sep 18 → build & run Sat Sep 19 → present 15:30

## 1. Problem

Published papers make quantitative claims ("X reduced Y by 23%"). Checking a claim means finding data, rebuilding an old software environment, understanding the method, redoing the analysis, and comparing. Humans rarely do it because it is slow and tedious. Prior work shows autonomous AI was bad at it: PaperBench (2025) best agent 21% vs ~41% for PhDs; Brodeur et al. (PNAS 2026) AI-led teams 57 pp below human teams, with a 37% autonomous reproduction rate.

Question this project answers, with numbers: **can a Claude Code agent replicate published results end-to-end without human help, and how far did Fable 5.1 move versus the previous frontier model (Claude Opus 5)?**

## 2. Goals

1. Run an identical, fixed agent scaffold over a ladder of replication tasks with two models, varying only the model.
2. Grade every attempt with an independent verifier that checks (a) the right thing was computed and (b) the number matches ground truth.
3. Produce one scorecard (pass/partial/fail × model, plus cost and time) and one chart, presentable in 3 minutes.
4. Surface at least one qualitative "gotcha" transcript: the older model fabricating or shortcutting where Fable 5.1 did not.

## 3. Non-goals

- Not a general-purpose research agent or product. No UI beyond the results dashboard.
- Not a full PaperBench/CORE-Bench run. Six tasks, hand-picked for a 5-hour window.
- No GPU. Everything runs on a laptop CPU or in the Claude Code sandbox.
- No fine-tuning, no prompt optimization per model. The scaffold is frozen after Friday's dry run.

## 4. Users

- Presenter (me): needs a reliable run script, a readable scorecard, a backup video.
- Audience / Anthropic staff in the room: want a sharp, credible finding about the new model and specific failure modes to take back to the model team.

## 5. Task ladder (already staged under `tasks/`)

| ID | Tier | Kind | Source | Ground truth |
|---|---|---|---|---|
| A1_hyperETA | A | Run authors' code, report MAPE/RMSE/MAE | CORE-Bench capsule-5367566 | gold runs in task.json |
| A2_admission_ensemble | A | Run `ensemble.py`, report macro precision/recall | CORE-Bench capsule-0238624 | gold runs in task.json |
| A3_culp | A | Run 3 scripts, report 6 accuracies | CORE-Bench capsule-6460826 | gold runs in task.json |
| B1_covid_mobility | B | Replicate "distancing cut mobility a further 23% (CI 20–27)" on new data | ReplicatorBench study 16 | `ground_truth/human_report.pdf` |
| B2_trump_distancing | B | Replicate "IQR ↑ Trump support → −4.1 pp distancing" on new data | ReplicatorBench study 1 | `ground_truth/human_report.*` |
| B3_branding_anova | B (backup) | Replicate Level × ProductType ANOVA interaction | ReplicatorBench study 23 | `ground_truth/human_report.docx` |
| C1_grokking | C (stretch) | From scratch: reproduce delayed generalization on mod-97 addition | Power et al. 2022 | criteria in task.json |

Tier A = code and data given. Tier B = paper + new data, agent designs the test. Tier C = paper only.

## 6. Functional requirements

### 6.1 Runner (`runner/run.py`) — exists, harden it
- R1. For each (model, task): copy `tasks/<task>/` to `work/<model>/<task>/` **excluding `ground_truth/`**. The agent must never see ground truth.
- R2. Invoke `claude -p <prompt.md> --model <model> --output-format json --max-turns 60 --permission-mode bypassPermissions --append-system-prompt <fixed suffix>` with cwd = the work dir.
- R3. Persist `run_meta.json`: cost_usd, duration_s, num_turns, session_id, returncode, timed_out, report_exists.
- R4. Per-run timeout 40 min; `--parallel N`; `--all` or `--tasks`. Exit early with a clear message if a Tier A capsule has not been fetched.
- R5. Idempotent re-runs: a rerun of (model, task) replaces the work dir; keep the previous `run_meta.json` as `run_meta.prev.json`.
- R6. Add `--dry-run` that prints the exact commands without executing.

### 6.2 Agent contract (in each `tasks/*/prompt.md`) — exists, keep stable
- Output is always `report.json` in the work dir with a `verdict` field and the task-specific numbers.
- Tier B additionally writes `preregistration.md` before analysis and `analysis.py`.
- Tier C writes `metrics.csv` and `grokking.png`.
- Rule text in every prompt: never report a number not observed in an output you produced.

### 6.3 Verifier (`verifier/verify.py`) — exists, harden it
- V1. Grader model is **fixed** (`claude-sonnet-5`) for all runs; configurable via `--grader`, logged into each `verdict.json`.
- V2. Tier A numeric matching is done in Python: answer within the span of gold runs ± 5% relative (or 5% when only one gold run). Strings compared case-insensitively.
- V3. The grader adjudicates fidelity (correct method vs proxy) and hallucination risk; it may open files in the work dir (report, code, outputs, paper).
- V4. Tier B: grader compares agent verdict to `human_verdict` in task.json. If `human_verdict` is unfilled, grader reads `ground_truth/human_report.*` (path passed in) and states it did so.
- V5. Output `verdict.json`: {fidelity, fidelity_reason, outcome ∈ pass|partial|fail, outcome_reason, hallucination_risk, precomputed, grader_model}.
- V6. If the grader returns malformed JSON, retry once, then write `outcome: fail` with `outcome_reason: "verifier error"` rather than crashing the batch.

### 6.4 Scorer (`scorer/score.py`) — exists
- S1. Aggregate to `results/results.json`: cells (model, task, tier, outcome, fidelity, agent_verdict, cost, wall, turns, reason) and per-model summary (pass, partial, fail, total, cost_usd, wall_min).
- S2. Inject results JSON into `dashboard/index.html` inside `<script id="data" type="application/json">` so the dashboard is a single self-contained file.

### 6.5 Dashboard (`dashboard/index.html`) — build this
- D1. Single HTML file, no build step, no external requests except Google Fonts. Renders from the embedded JSON.
- D2. Hero: one sentence finding, auto-generated from summary ("Fable 5.1 replicated 5 of 6; Opus 5 replicated 2 of 6") plus total cost and minutes per model.
- D3. Scorecard table: rows = tasks grouped by tier, columns = models, cell = outcome badge + cost + minutes; hover/tap reveals `outcome_reason`.
- D4. One chart: pass count by tier per model, inline SVG, no chart library.
- D5. "Gotcha" panel: a side-by-side of two short transcript excerpts (from `work/<model>/<task>/`) chosen by hand via a small `dashboard/highlights.json` file: {task, old_excerpt, new_excerpt, caption}.
- D6. Works on a projector: min font 16px, high contrast, light and dark via `prefers-color-scheme`. Fits one 16:9 screen without scrolling for 6 tasks × 2 models.
- D7. Empty/partial state: cells not yet run show "queued"; the page must look intentional at 9:30 AM with only the baseline column filled.

### 6.6 Prep scripts
- P1. `scripts/fetch_all.sh`: runs every `tasks/A*/fetch.sh`.
- P2. `scripts/friday.sh`: fetch_all → run baseline model on all tasks → verify → score. Prints a go/no-go summary: which tasks produced a report, which passed.
- P3. `scripts/saturday.sh <model>`: run only the new model → verify both → score. Prints the same summary.
- P4. `scripts/record_backup.md`: checklist to screen-record the dashboard as fallback video.

## 7. Non-functional requirements

- N1. Reproducible: pin the scaffold (prompts, turn limit, system suffix) in git; the commit hash appears in `results.json` and in the dashboard footer.
- N2. Cost ceiling: ≤ $8 per run flagged, ≤ $60 total across both models. Log every run's cost.
- N3. Time: Friday dry run ≤ 3 hours wall; Saturday new-model column ≤ 2.5 hours with `--parallel 3`.
- N4. No secrets in the repo. API auth via Claude Code login or `ANTHROPIC_API_KEY` env var.
- N5. Python 3.11+, standard library only for runner/verifier/scorer. Agent-side libraries are installed by the agent in its own work dir.

## 8. Success metrics

- M1. Friday: harness runs end to end on baseline; ≥ 4 of 6 tasks produce a `report.json`; verifier grades all of them without manual intervention.
- M2. Saturday: Fable column complete by 13:00; scorecard and chart rendered; at least one clear difference between models (any tier) or an honest "no difference at this tier" statement.
- M3. Presentation: 3-minute demo with one headline sentence, the scorecard, one gotcha transcript, and cost/time. Backup video recorded by 15:00.
- M4. Hand-off: a two-sentence summary plus one PNG (scorecard or grokking curve) in `results/recap/` for the organizers' roll-up.

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Both models pass everything → no story | Ladder has headroom (B3, C1). Friday decides which tasks stay. |
| Capsules fail to build (old deps) | That is the test; but if a Tier A task fails for *both* models on Friday for environment reasons unrelated to the agent, swap it for another CORE-Bench Python capsule. |
| Runs exceed time on Saturday | `--parallel 3`, 40-min timeout, start runs at 9:15 before building the dashboard. |
| Verifier grades wrongly | Tier A numeric check is deterministic; spot-check every Tier B verdict by hand against the human report. |
| Live demo fails | Dashboard is static; backup video recorded at 15:00. |
| Cost overrun | Per-run flag at $8; watch `run_meta.json` totals after the first two runs. |

## 10. Timeline

**Fri Sep 18 (evening, ~4 h)**
1. `scripts/fetch_all.sh`; read `ground_truth/human_report.*` for B1, B2, B3 and fill `human_verdict` in each task.json. Ensure at least one B task is `not_replicated` by human standards.
2. Build dashboard (D1–D7) with fake data first, then real.
3. `scripts/friday.sh` with baseline `claude-opus-5`. Review go/no-go. Freeze scaffold; tag commit `baseline`.

**Sat Sep 19**
- 09:00 arrive, credits, network check. 09:15 `scripts/saturday.sh claude-fable-5-1`.
- 09:15–10:30 polish dashboard while runs go; pick gotcha candidates from baseline transcripts.
- 10:30–13:00 rerun failures once, verify, score. If ≥ 4 pass and time permits, launch C1.
- 13:00–14:30 grokking or polish; write headline sentence; export recap PNG + blurb.
- 14:30–15:00 record backup video. 15:00–15:30 rehearse twice. 15:30 present.

## 11. Repo layout

```
replication-bench/
  PRD.md                 this file
  README.md              quickstart
  tasks/<id>/            task.json, prompt.md, (fetch.sh | data + paper), ground_truth/ (B only)
  runner/run.py          R1–R6
  verifier/verify.py     V1–V6
  scorer/score.py        S1–S2
  dashboard/index.html   D1–D7   dashboard/highlights.json  D5
  scripts/               P1–P4
  work/<model>/<task>/   generated: agent output, report.json, run_meta.json, verdict.json
  results/               results.json, recap/
```

## 12. Instructions to Claude Code

Read this PRD and the existing files under `runner/`, `verifier/`, `scorer/`, `tasks/`. Then, in order: (1) implement `scripts/` P1–P4; (2) build `dashboard/index.html` per D1–D7 with a fixture `results/results.sample.json` so it renders before any runs exist; (3) harden `runner/run.py` (R5, R6) and `verifier/verify.py` (V6); (4) add N1 commit-hash stamping to the scorer; (5) write `README.md` with the three commands a tired person needs at 9:15 AM. Do not change any `tasks/*/prompt.md` without flagging it, because the prompts are part of the frozen scaffold. Ask before spending API credits.
