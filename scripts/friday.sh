#!/usr/bin/env bash
# P2: Friday dry run — fetch capsules, run the BASELINE model on all tasks, verify, score.
# Usage: scripts/friday.sh [baseline-model]      (default: claude-opus-5)
set -euo pipefail
cd "$(dirname "$0")/.."
BASELINE="${1:-claude-opus-5}"

echo "== 1/4 fetch Tier A capsules =="
bash scripts/fetch_all.sh

echo "== 2/4 run baseline: $BASELINE on all tasks =="
python3 runner/run.py --all --models "$BASELINE" --parallel 3

echo "== 3/4 verify =="
python3 verifier/verify.py --models "$BASELINE"

echo "== 4/4 score =="
python3 scorer/score.py

echo
echo "== GO / NO-GO summary ($BASELINE) =="
python3 - "$BASELINE" <<'EOF'
import json, sys
from pathlib import Path
model = sys.argv[1]
work = Path("work") / model
rows, reports, passes = [], 0, 0
for d in sorted(work.iterdir()) if work.exists() else []:
    if not d.is_dir():
        continue
    meta = json.loads((d / "run_meta.json").read_text()) if (d / "run_meta.json").exists() else {}
    verd = json.loads((d / "verdict.json").read_text()) if (d / "verdict.json").exists() else {}
    has_report = (d / "report.json").exists()
    reports += has_report
    outcome = verd.get("outcome", "ungraded")
    passes += outcome == "pass"
    flag = " OVER-BUDGET" if meta.get("over_budget") else ""
    rows.append(f"  {d.name:24s} report={'yes' if has_report else 'NO ':3s} outcome={outcome:8s} "
                f"cost=${meta.get('cost_usd') or 0:.2f}{flag}")
print("\n".join(rows) or "  (no runs found)")
n = len(rows)
print(f"\n  {reports}/{n} produced report.json; {passes}/{n} passed.")
print("  GO" if reports >= 4 else "  NO-GO: fewer than 4 reports (PRD M1). Investigate before freezing the scaffold.")
EOF

echo
echo "Next: review verdicts, pick gotcha candidates, then freeze: git tag baseline"
