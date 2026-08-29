# Risk Intelligence Platform — Backend + ML

A FastAPI + scikit-learn/XGBoost backend implementing:

1. **Explainable Fraud Agent** — scores a transaction, explains *why* via SHAP.
2. **Merchant Risk Investigator** — aggregates transactions into risk profiles
   for a derived entity grouping (see [Known Limitations](#known-limitations)
   — IEEE-CIS has no real merchant ID).
3. **Real-time Transaction Copilot** — natural-language Q&A over scored
   transactions/entities, backed by a deterministic template engine by
   default, with an optional LLM abstraction layer.

This is a **backend + ML** deliverable only. The frontend is a separate
React app that consumes the REST API described below.

---

## 1. Folder structure

```
backend/
├── app/
│   ├── main.py                     FastAPI app, CORS, startup, /api/health
│   ├── api/
│   │   ├── routes_transactions.py  GET/POST /api/transactions...
│   │   ├── routes_merchants.py     GET /api/merchants...
│   │   ├── routes_risk.py          GET/POST /api/risk...
│   │   ├── routes_copilot.py       POST /api/copilot
│   │   ├── routes_analytics.py     GET /api/analytics...
│   │   └── routes_audit.py         GET/POST /api/audit-logs
│   ├── core/
│   │   └── config.py               Settings, all env-var driven
│   ├── models/
│   │   └── schemas.py              Pydantic request/response models
│   ├── services/
│   │   ├── fraud_service.py        Orchestrates score→risk→decision→explain→persist
│   │   ├── merchant_service.py     Derived-entity aggregation & investigation
│   │   ├── risk_service.py         probability→score→level→decision mapping
│   │   ├── copilot_service.py      LLM abstraction + deterministic fallback
│   │   └── audit_service.py        Audit log CRUD
│   ├── ml/
│   │   ├── preprocessing.py        ColumnTransformer (numeric/categorical)
│   │   ├── feature_engineering.py  All engineered features + docs
│   │   ├── feature_selection.py    Variance/corr/MI/RF/SHAP → combined ranking
│   │   ├── train.py                Full training entrypoint (`python -m app.ml.train`)
│   │   ├── evaluate.py             Metrics + plots (confusion matrix, ROC, PR, SHAP)
│   │   ├── explain.py              SHAP-based per-transaction explanations
│   │   └── predict.py              Loads saved artifacts, scores new transactions
│   ├── data/
│   │   └── loader.py               Load/validate/join IEEE-CIS CSVs (+ synthetic fallback)
│   └── database/
│       ├── database.py             SQLAlchemy engine/session (SQLite → Postgres-ready)
│       └── models.py               AuditLog, ScoredTransaction ORM models
├── data/                           Place Kaggle CSVs here (see data/README.md)
├── models/                         Saved model artifacts (created by training)
├── reports/                        Saved evaluation plots/metrics (created by training)
├── tests/
│   ├── test_pipeline.py            Dataset/feature/risk/merchant unit tests
│   └── test_api.py                 API endpoint tests (FastAPI TestClient)
├── requirements.txt
├── .env.example
└── README.md                       (this file)
```

---

## 2. Requirements

See `requirements.txt`:

```
fastapi, uvicorn, pydantic, sqlalchemy, pandas, numpy, scikit-learn,
xgboost, shap, matplotlib, joblib, python-multipart, python-dotenv,
pytest, httpx, anthropic
```

Install:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

> `xgboost` and `shap` are used opportunistically — the code degrades
> gracefully (logs a warning and skips that method) if either package is
> unavailable in your environment, so the pipeline still runs end-to-end
> without them.

---

## 3. Environment variables

Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
```

Key variables: `DATA_DIR`, `MODEL_DIR`, `REPORTS_DIR`, `DATABASE_URL`,
`RISK_LOW_MAX` / `RISK_MEDIUM_MAX` / `RISK_HIGH_MAX` (score thresholds),
`N_SELECTED_FEATURES`, `ALLOW_SYNTHETIC_FALLBACK`, `LLM_API_KEY` /
`LLM_PROVIDER` / `LLM_MODEL` (Copilot LLM mode, optional), `CORS_ORIGINS`.

---

## 4. Dataset placement

See `data/README.md`. In short: download IEEE-CIS Fraud Detection from
Kaggle and place `train_transaction.csv`, `train_identity.csv`,
`test_transaction.csv`, `test_identity.csv` under `backend/data/`.

**If the real files are absent**, `app/data/loader.py` automatically falls
back to a small synthetic dataset with the same schema (governed by
`ALLOW_SYNTHETIC_FALLBACK` / `SYNTHETIC_ROWS`) so the full pipeline is
runnable for development. Every place this happens is logged loudly and
surfaced via `"data_source": "synthetic"` in API/metadata responses — it is
never silently presented as real data. **This repository was built and
smoke-tested in a sandboxed environment without network/Kaggle access, so
the numbers in `reports/` right now come from that synthetic fallback.**
Re-run training with the real CSVs in place for a model with actual
predictive validity.

---

## 5. Training

```bash
python -m app.ml.train
```

This runs the full STEP 1–8/21 pipeline: load → validate → feature-engineer
→ time-aware split → preprocess (fit on train only) → feature-select →
train & compare Logistic Regression / Random Forest / XGBoost (if installed)
→ evaluate best model (by validation PR-AUC) on the held-out test split →
save plots to `reports/` → save `models/fraud_model.pkl`,
`preprocessor.pkl`, `selected_features.json`, `model_metadata.json`.

Console output includes the dataset report, feature-selection summary, and
per-model validation PR-AUC/ROC-AUC comparison.

## 6. Evaluation

Evaluation runs automatically at the end of `train.py` (on the held-out test
split) and writes to `reports/`:

- `metrics.json` — precision, recall (fraud), F1, ROC-AUC, PR-AUC, confusion matrix
- `confusion_matrix.png`
- `roc_curve.png`
- `precision_recall_curve.png`
- `feature_importance.png`
- `shap_summary.png` (if `shap` is installed)

To re-evaluate a saved model against a fresh dataset without retraining, use
`app.ml.evaluate.evaluate_model(y_true, y_proba)` directly in a notebook/script.

## 7. Running the backend

```bash
uvicorn app.main:app --reload --port 8000
```

Then visit `http://localhost:8000/docs` for interactive Swagger docs.
`GET /api/health` reports whether a trained model is loaded.

## 8. Running tests

```bash
pytest -v
```

`tests/test_pipeline.py` covers dataset loading/validation, feature
engineering (incl. a target-leakage check), risk-score/decision boundary
values, and merchant aggregation — no server needs to be running.
`tests/test_api.py` uses FastAPI's `TestClient` to exercise every route,
including invalid input (422), unknown transaction/merchant (404), and the
"model not trained yet" (503) path.

---

## 9. API documentation

All responses are JSON. Base URL: `http://localhost:8000`.

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Service + model-loaded status |
| GET | `/api/transactions` | List previously-scored transactions (paginated) |
| GET | `/api/transactions/{id}` | Get a previously-scored transaction |
| POST | `/api/transactions/predict` | Score a new transaction (Explainable Fraud Agent) |
| GET | `/api/risk/{id}` | Get risk/decision for a scored transaction |
| POST | `/api/risk/decision` | Record/override a final decision (writes audit log) |
| GET | `/api/merchants` | List derived entities, ranked by risk |
| GET | `/api/merchants/{id}` | Full merchant/entity investigation |
| GET | `/api/merchants/{id}/risk` | Merchant/entity risk summary only |
| POST | `/api/copilot` | Natural-language Q&A over a transaction/entity |
| GET | `/api/analytics/overview` | Aggregate counts/rates over scored transactions |
| GET | `/api/analytics/model-performance` | Trained model's saved metrics |
| GET | `/api/analytics/risk-distribution` | Count of scored transactions per risk level |
| GET | `/api/audit-logs` | List audit log entries |
| POST | `/api/audit-logs` | Create an audit log entry directly |

### Example: `POST /api/transactions/predict`

Request:
```json
{
  "TransactionAmt": 850.75,
  "TransactionDT": 5000000,
  "ProductCD": "W",
  "card1": 12000,
  "card4": "visa",
  "card6": "credit",
  "P_emaildomain": "gmail.com"
}
```

Response:
```json
{
  "transaction_id": "TXN-3F9A21B0",
  "fraud_probability": 0.0231,
  "risk_score": 2,
  "risk_level": "LOW",
  "recommended_decision": "ALLOW",
  "decision_reason": "Risk level classified as LOW, mapped to ALLOW per current policy thresholds. Primary driver: Log1p of TransactionAmt — compresses the heavy right tail of amounts.",
  "risk_factors": [
    {"feature": "amount_log", "impact": -3.74, "direction": "decrease", "description": "Log1p of TransactionAmt — compresses the heavy right tail of amounts."},
    {"feature": "amount_percentile", "impact": 2.07, "direction": "increase", "description": "Percentile rank (0-1) of this transaction's amount within the full dataset."}
  ],
  "explanation": "This transaction was scored LOW risk, resulting in a ALLOW decision. The strongest contributing signals were: ...",
  "data_source": "synthetic"
}
```

### Example: `POST /api/copilot`

Request:
```json
{ "message": "Why was this flagged?", "transaction_id": "TXN-3F9A21B0" }
```

Response:
```json
{
  "answer": "Transaction TXN-3F9A21B0 was scored at risk level LOW (risk score 2/100, model fraud probability 2.31%), leading to a recommended decision of ALLOW. ...",
  "risk_score": 2,
  "decision": "ALLOW",
  "key_findings": ["Risk level: LOW", "Recommended decision: ALLOW", "Model fraud probability: 2.31%"],
  "evidence": [{"type": "model_score", "detail": {"...": "..."}}],
  "recommended_action": "No action required; continue standard processing.",
  "engine": "deterministic_template"
}
```

---

## 10. Database schema

SQLite by default (`DATABASE_URL`), Postgres-ready (swap the URL, same models).

**`audit_logs`**: `id`, `timestamp`, `transaction_id`, `previous_decision`,
`new_decision`, `risk_score`, `actor`, `reason`.

**`scored_transactions`**: `id`, `transaction_id` (unique), `fraud_probability`,
`risk_score`, `risk_level`, `recommended_decision`, `final_decision`,
`explanation`, `raw_payload_json`, `created_at`.

---

## 11. Model performance report

Generated at `reports/metrics.json` + PNG plots after each training run. The
current artifacts in this repo were produced on the **synthetic fallback
dataset** (see §4) because this environment had no network access to
download the real Kaggle files — treat the current numbers as a pipeline
smoke test, not a real fraud-detection result. Re-run `python -m app.ml.train`
after placing the real CSVs to get a meaningful report; the same code path
will then report actual precision/recall/F1/ROC-AUC/PR-AUC on real data
without any changes.

---

## 12. Frontend integration

The React frontend should call the REST endpoints in §9 over HTTP(S) with
`fetch`/`axios`. `CORS_ORIGINS` in `.env` must include the frontend's origin
(default `http://localhost:3000`). A typical flow:

1. User submits a transaction form → `POST /api/transactions/predict` →
   render `risk_score`, `risk_level`, `recommended_decision`, `risk_factors`.
2. Analyst reviews → `POST /api/risk/decision` to record a final decision
   (auto-writes an audit log entry).
3. Merchant dashboard → `GET /api/merchants` (list) → `GET /api/merchants/{id}`
   (drill-down investigation view).
4. Chat-style panel → `POST /api/copilot` with the current `transaction_id`
   or `merchant_id` in context.
5. Analytics dashboard → the three `/api/analytics/*` endpoints.

No frontend code is included in this deliverable.

---

## 13. Known limitations

- **No real merchant ID in IEEE-CIS.** `merchant_service.py` derives a proxy
  grouping from `(ProductCD, card4, card6)`. Every merchant response is
  labeled with `grouping_strategy` and a `limitations` string — this is not
  verified merchant identity and should not be presented as such in
  production.
- **V1-V339 and most C/D columns are anonymized** by Kaggle with no
  disclosed real-world meaning. The explainability layer describes these
  generically ("anonymized dataset signal") rather than inventing semantics.
- **This repo currently ships trained on synthetic fallback data** (see §4/§11)
  because the sandbox this was built in has no internet access to fetch the
  real ~590MB Kaggle dataset. The architecture, preprocessing, feature
  engineering, and evaluation code are unchanged either way — only the input
  CSVs differ.
- **Analytics endpoints reflect only transactions scored through this API's
  database**, not the full training dataset, since IEEE-CIS itself has no
  natural "live traffic" concept.
- **Copilot's LLM mode is a thin, best-effort abstraction** (Anthropic only,
  wired as an example) — it is not required; the deterministic template
  engine is the default and always available.
- **`TransactionDT` is a relative offset**, not a real calendar timestamp
  (per Kaggle's documentation), so `hour`/`day_of_week` features represent
  cyclical position, not literal wall-clock time.

## 14. Future improvements

- Add a true production merchant/seller identifier if integrating with a
  real payments system (this dataset alone can't provide one).
- Add authentication/authorization (API keys or OAuth) before any real
  deployment — none is implemented here beyond input validation and CORS.
- Add model monitoring / drift detection and a retraining schedule.
- Add pagination cursors and rate limiting for `/api/transactions` and
  `/api/merchants` at scale.
- Swap SQLite → PostgreSQL for concurrent production use (`DATABASE_URL`
  already supports this with no code changes).
- Add a proper LLM provider abstraction (OpenAI, etc.) beyond the Anthropic
  example wired into `copilot_service.py`.
