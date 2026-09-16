# Task: replicate the "grokking" phenomenon from scratch

Paper: Power et al., "Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets" (arXiv 2201.02177). No code or data are provided.

Claim to replicate: a small transformer trained on modular addition (a + b mod p, p = 97) with about half the pairs as training data first memorizes the training set (train accuracy ~100%, validation near chance) and then, much later, abruptly generalizes (validation accuracy jumps to ~100%). Weight decay matters.

Steps:
1. Implement the dataset and a small transformer (1-2 layers, width ~128) in PyTorch. CPU only.
2. Train with AdamW, weight decay ~1.0, and log train/val accuracy every N steps to `metrics.csv`.
3. Budget: 30 minutes wall time max. Choose learning rate, batch size and number of steps so grokking can plausibly appear in that budget (fraction of data ~0.5, full-batch or large batches help).
4. Produce `grokking.png`: train and val accuracy vs step (log-x is fine).
5. Write `report.json`:

```json
{
  "step_train_acc_99": <int or null>, "step_val_acc_95": <int or null>,
  "final_train_acc": <float>, "final_val_acc": <float>,
  "delay_ratio": <step_val_95 / step_train_99 or null>,
  "verdict": "replicated" | "not_replicated" | "could_not_test",
  "config": {...}, "notes": "..."
}
```

Criterion: replicated if val accuracy reaches 0.95 and does so at least 2x later (in steps) than train accuracy reached 0.99.
