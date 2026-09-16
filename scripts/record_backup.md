# P4: Backup video checklist (target: recorded by 15:00 Sat)

Goal: a ~90-second screen recording of the dashboard that can replace the live demo.

## Before recording
- [ ] `python3 scorer/score.py` one last time so `dashboard/index.html` holds the final numbers.
- [ ] Open `dashboard/index.html` in a clean browser window (no bookmarks bar, no other tabs).
- [ ] Check the footer shows the frozen commit hash (not `-dirty`, not `no-git`). If dirty: commit, re-score.
- [ ] Confirm the gotcha panel shows real excerpts (edit `dashboard/highlights.json`, re-run `scorer/score.py`).
- [ ] Set display to the projector resolution (1920×1080) and confirm the page fits without scrolling.
- [ ] Try both themes (macOS: System Settings → Appearance) and pick the one that reads better on the projector.

## Recording (macOS)
- [ ] Cmd+Shift+5 → "Record Selected Portion" → select the browser window → Record.
- [ ] Script, ~90 s total:
  1. (10 s) Hero sentence — read it out loud, it is the headline.
  2. (30 s) Scorecard — hover the one or two most telling cells so the verifier reason shows.
  3. (15 s) Chart — passes by tier, point at the tier where the models diverge.
  4. (25 s) Gotcha panel — read the baseline excerpt, then the new model's.
  5. (10 s) Footer — commit hash + fixed grader = reproducible.
- [ ] Stop, save as `results/recap/backup_demo.mov`.

## After recording
- [ ] Play it back once, with sound off, at 100% size.
- [ ] Copy to a second location (AirDrop to phone or USB stick).
- [ ] Export recap PNG: screenshot the scorecard (Cmd+Shift+4) → `results/recap/scorecard.png`.
- [ ] Write the two-sentence summary for organizers in `results/recap/summary.txt` (M4).
