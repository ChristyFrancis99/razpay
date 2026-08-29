# Dataset placement

Download the **IEEE-CIS Fraud Detection** dataset from Kaggle:
https://www.kaggle.com/c/ieee-fraud-detection/data

Place these files directly in this `data/` folder:

```
data/
  train_transaction.csv
  train_identity.csv
  test_transaction.csv
  test_identity.csv
  sample_submission.csv   (optional, not used by this backend)
```

If these files are **not** present, `app/data/loader.py` will automatically
fall back to a small synthetic dataset with the same column schema (see
`ALLOW_SYNTHETIC_FALLBACK` / `SYNTHETIC_ROWS` in `.env`). This lets you run
the full pipeline end-to-end for development, but **the resulting model has
no real fraud-detection validity** — every API response and the training
metadata will show `"data_source": "synthetic"` so this is never mistaken
for a real result. Train on the real files for a meaningful model.
