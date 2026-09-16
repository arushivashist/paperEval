# Task: reproduce results from "HyperETA: A Non–Deep Learning Method for Estimated Time of Arrival"

You are in a working directory containing the authors' code repository (folder `capsule/`).
Your job is to computationally reproduce the paper's results and report specific numbers.

Original instruction from the benchmark:
> Run run.ipynb and convert the results to html.

Steps:
1. Inspect the repository. Install whatever dependencies are needed (no GPU available).
2. Run the code as instructed. If something breaks, fix the environment or the code minimally; note every change.
3. Find the outputs and answer each question below exactly as the outputs state them.
4. Write `report.json` in the working directory with this shape:

```json
{
  "answers": {"<question text>": <number or string>, ...},
  "verdict": "reproduced" | "partially_reproduced" | "failed",
  "confidence": 0.0-1.0,
  "what_i_ran": "commands and files executed",
  "deviations": "anything you changed or could not run",
  "notes": "brief"
}
```

Questions:
- Report the HyperETA MAPE with no DTW.
- Report the HyperETA RMSE with no DTW.
- Report the HyperETA MAE with no DTW.

Rules: do not guess numbers you did not observe in the outputs. If you cannot produce a number, set it to null and say why in `deviations`.
