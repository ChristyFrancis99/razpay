# Local IEEE-CIS dataset

The backend looks for the IEEE-CIS Fraud Detection CSVs in `backend/data/` first. For compatibility with the existing repository layout, it also detects a local `ieee-fraud-detection/` folder at the repository root when `backend/data/train_transaction.csv` is not present.

Preferred layout:

```text
data/
  train_transaction.csv
  train_identity.csv
  test_transaction.csv        # optional
  test_identity.csv           # optional
  sample_submission.csv       # optional, not used by this backend
```

The large CSV files are intentionally ignored by Git. Keep them on the local development machine (or a private data store), not in the public repository.

## Populate the dashboard

After the trained model artifacts are present, run from the `backend/` directory:

```bash
python -m scripts.seed_demo_data
```

The seed script reads the large training CSVs in chunks, selects a representative sample, runs each selected transaction through the same production inference pipeline used by `POST /api/transactions/predict`, and stores only the scored results in the local SQLite database.

The script **does not silently fall back to synthetic data**. If the real IEEE-CIS CSVs are missing, it stops and tells you where they must be placed.

Useful options:

```bash
python -m scripts.seed_demo_data --rows 100 --candidate-pool 400
python -m scripts.seed_demo_data --rows 150 --candidate-pool 600 --seed 42
```

For a disposable local demo database only, `--clear` removes existing scored transactions before reseeding:

```bash
python -m scripts.seed_demo_data --clear
```

Do not use `--clear` against a database containing real investigation history.

## Synthetic fallback

The application's normal data loader still supports its existing synthetic fallback for development when the real dataset is unavailable. That fallback is separate from the demo seeder and must not be presented as real IEEE-CIS evaluation data.
