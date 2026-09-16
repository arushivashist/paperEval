# Task: replicate a published claim using a new dataset

Working directory contents:
- `original_paper.pdf`: the published paper.
- `initial_details.txt`: short orientation notes (if present).
- `replication_data/`: a NEW dataset collected or assembled for replication, plus possibly reference scripts. Prefer writing your own analysis; only consult scripts if stuck, and say so.

The focal claim to test:
> ...products supporting predominantly utilitarian category-level attitudes supported somewhat more symbolic attitudes when branded, whereas products supporting predominantly symbolic category-level attitudes supported less symbolic attitudes when branded…predicted level ×product type interaction (F(1, 204) = 7.70, p = .006).

Hypothesis as stated by the authors:
> Products predominantly associated with utilitarian attitudes at the category level support less utilitarian and more symbolic attitudes at the brand level. Products predominantly associated with symbolic attitudes at the category level support less symbolic and more utilitarian attitudes at the brand level.

Steps:
1. Read the paper enough to understand the exact statistical test behind the focal claim (variables, model, controls, sample).
2. Inspect the replication data. Map the paper's variables to columns. Note mismatches.
3. Pre-register your plan in `preregistration.md` BEFORE running the test: the exact model, the outcome, the coefficient of interest, and the criterion you will use to call it replicated.
4. Run the analysis in Python (or R if unavoidable). Save code in `analysis.py`.
5. Write `report.json`:

```json
{
  "focal_estimate": <number>, "se_or_ci": "<text>", "p_value": <number or null>, "n": <int>,
  "original_estimate": "<from the paper>",
  "verdict": "replicated" | "not_replicated" | "mixed" | "could_not_test",
  "reasoning": "2-4 sentences on why",
  "deviations": "data or method differences from the original",
  "confidence": 0.0-1.0
}
```

Rules: a claim is not "replicated" just because the sign matches. Apply the criterion you pre-registered. If the data cannot support the test, say `could_not_test` and explain.
