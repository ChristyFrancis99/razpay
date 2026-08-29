# Razorpay Risk Intelligence Platform

AI-assisted fraud and AML operations platform built around the IEEE-CIS transaction model, explainable risk scoring, merchant investigation, transaction copilot, and auditable human decisions.

## Architecture

- `backend/` — FastAPI API, SQLite persistence, risk engine, ML prediction/explanation, merchant investigator and copilot.
- `frontend/` — TanStack Start + React 19 + TypeScript + Tailwind dashboard.
- `ieee-fraud-detection/` — training/research assets.

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000` and health is exposed at `/api/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Copy `frontend/.env.example` to `.env` when the frontend and backend run on different origins.

## Main workflow

1. Start the FastAPI backend.
2. Score transactions through `POST /api/transactions/predict`.
3. The dashboard reads scored transactions and analytics from the API.
4. Investigators open a transaction and choose Allow, Review or Hold.
5. Decisions are persisted and written to `/api/audit-logs`.
6. Copilot answers evidence-oriented questions using `/api/copilot`.

## Model note

If real IEEE-CIS files are unavailable, the backend can use its configured synthetic fallback for development/demo operation. Do not present synthetic evaluation metrics as production performance.
