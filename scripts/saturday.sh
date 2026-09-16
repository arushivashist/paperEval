#!/usr/bin/env bash
# P3: Saturday run — run ONLY the new model, verify both columns, score.
# Usage: scripts/saturday.sh <new-model> [baseline-model]
#    eg: scripts/saturday.sh claude-fable-5-1
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -ge 1 ] || { echo "usage: scripts/saturday.sh <new-model> [baseline-model]"; exit 1; }
NEW="$1"
BASELINE="${2:-claude-opus-5}"

echo "== 1/3 run new model: $NEW on all tasks =="
python3 runner/run.py --all --models "$NEW" --parallel 3

echo "== 2/3 verify both models =="
python3 verifier/verify.py --models "$BASELINE" "$NEW"

echo "== 3/3 score =="
python3 scorer/score.py

echo
echo "== summary ($NEW vs $BASELINE) =="
python3 - "$NEW" "$BASELINE" <<'EOF'
import json, sys
from pathlib import Path
for model in sys.argv[1:]:
    work = Path("work") / model
    if not work.exists():
        print(f"[{model}] no runs")
        continue
    print(f"[{model}]")
    reports = passes = n = 0
    for d in sorted(work.iterdir()):
        if not d.is_dir():
            continue
        n += 1
        meta = json.loads((d / "run_meta.json").read_text()) if (d / "run_meta.json").exists() else {}
        verd = json.loads((d / "verdict.json").read_text()) if (d / "verdict.json").exists() else {}
        has_report = (d / "report.json").exists()
        reports += has_report
        outcome = verd.get("outcome", "ungraded")
        passes += outcome == "pass"
        flag = " OVER-BUDGET" if meta.get("over_budget") else ""
        print(f"  {d.name:24s} report={'yes' if has_report else 'NO ':3s} outcome={outcome:8s} "
              f"cost=${meta.get('cost_usd') or 0:.2f}{flag}")
    print(f"  -> {reports}/{n} reports, {passes}/{n} pass\n")
EOF

echo "Dashboard refreshed: open dashboard/index.html"
echo "Reruns: python3 runner/run.py --tasks <id> --models $NEW   (then verify + score again)"
