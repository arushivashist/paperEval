# Task: reproduce results from "CULP: Classification Using Link Prediction"

You are in a working directory containing the authors' code repository (folder `capsule/`).
Your job is to computationally reproduce the paper's results and report specific numbers.

Original instruction from the benchmark:
> Run 'iris_sample.py', 'zoo_sample.py', and 'wine_sample.py'

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
- Report the CN prediction accuracy for the Iris dataset.
- Report the AA prediction acccuracy for the Iris dataset.
- Report the CN prediction acccuracy for the Zoo dataset.
- Report the AA prediction acccuracy for the Zoo dataset.
- Report the CN prediction acccuracy for the Wine dataset.
- Report the AA prediction acccuracy for the Wine dataset.

Rules: do not guess numbers you did not observe in the outputs. If you cannot produce a number, set it to null and say why in `deviations`.
