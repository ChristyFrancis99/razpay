# Razorpay Risk Intelligence Platform

## About the Project

Razorpay Risk Intelligence is an explainable fraud, AML, and transaction-risk operations platform designed to help investigators identify suspicious transactions, assess merchant risk, support human decision-making, and maintain an auditable record of risk decisions.

The platform combines a machine-learning fraud prediction model with a risk-scoring and investigation layer. Instead of producing only a binary fraud prediction, the system converts model output into fraud probability, risk score, risk level, recommended action, risk factors, and an explanation that can be reviewed by a human investigator.

The core workflow is:

```text
Transaction
    |
    v
Machine Learning Model
    |
    v
Fraud Probability
    |
    v
Risk Scoring Engine
    |
    +------------------+
    |                  |
    v                  v
Risk Factors       Recommendation
                       |
                       v
              Human Investigation
                       |
             +---------+---------+
             |         |         |
             v         v         v
           ALLOW     REVIEW     HOLD
                       |
                       v
                  Audit Trail
```

The project supports transaction-level risk investigation, merchant-level risk analysis, an investigator-oriented Copilot, authentication, role-based functionality, and audit logging.

## Features

### Risk Operations Dashboard

- Centralized risk overview
- Total transaction count
- Fraud transaction count
- High-risk and critical transaction counts
- Risk distribution
- Decision distribution
- Model readiness
- System health

### Transaction Fraud Detection

Transactions can be processed through the trained fraud-detection model to generate:

- Fraud probability
- Risk score
- Risk level
- Recommended decision
- Risk factors
- Explainable reasoning

### Transaction Investigation

Investigators can select a transaction and inspect its risk information before making a decision.

Risk levels:

- LOW
- MEDIUM
- HIGH
- CRITICAL

Decision mapping:

- LOW → ALLOW
- MEDIUM → REVIEW
- HIGH → REVIEW
- CRITICAL → HOLD

### Human-in-the-Loop Decisions

The system is designed so that the machine-learning model provides a recommendation while the investigator remains responsible for the final operational decision.

```text
AI Recommendation → Human Review → Final Decision
```

Investigators can record decisions such as Allow, Review, or Hold and provide a reason for the decision.

### Merchant Risk Investigation

Provides merchant-level analysis in addition to individual transaction investigation. This helps identify merchants with unusual activity or elevated fraud risk.

### Transaction Copilot

Provides an investigator-oriented interface for asking questions about transaction or merchant risk and receiving evidence-oriented findings and recommended actions.

### Audit Trail

Records important risk decisions and human interventions for traceability and accountability, including transaction, previous decision, new decision, risk score, actor, reason, and timestamp.

### Authentication and Roles

Supports authenticated operational users and role-based functionality, including Administrator, Investigator, and Manager roles.

### System Health

Provides backend, database, and model-readiness information so that the operational state of the platform can be monitored.

### IEEE-CIS Dataset Integration

The project uses the IEEE-CIS Fraud Detection dataset for the fraud-detection workflow. The full dataset remains local and is not required to be committed to GitHub.

The demo seeder can read representative IEEE-CIS transactions in chunks, run them through the same inference pipeline used by the application, and store the resulting scored transactions in the local database.

## Advantages

- Provides explainable risk decisions instead of only binary fraud predictions.
- Keeps a human investigator involved in important decisions.
- Combines transaction-level and merchant-level investigation.
- Maintains an audit trail for decisions and overrides.
- Integrates the ML model into a complete application instead of limiting it to a notebook.
- Separates frontend, backend, database, and ML responsibilities through APIs and services.
- Provides a centralized interface for fraud and AML operations.
- Does not require the large IEEE-CIS dataset to be stored in the GitHub repository.
- Can be extended with additional models, data sources, and investigation workflows.

## Limitations and Cons

- Model performance depends on the quality and representativeness of the training data.
- The IEEE-CIS dataset is historical and may not represent all current fraud patterns.
- Logistic Regression may not model complex nonlinear relationships as effectively as more advanced ensemble or deep-learning approaches.
- Predictions can contain false positives and false negatives and should not be treated as absolute truth.
- The current implementation is primarily a research, demonstration, and prototype platform rather than a production financial-risk system.
- Production deployment would require stronger secrets management, infrastructure security, monitoring, logging, rate limiting, and compliance controls.
- Full external-LLM Copilot functionality requires the appropriate LLM configuration and credentials.
- Large-scale workloads would require additional database, caching, queueing, and deployment optimization.
- Real financial systems require extensive regulatory, privacy, security, and governance controls beyond the scope of this project.

## Technology Stack

### Frontend

- React 19
- TypeScript
- TanStack Start
- TanStack Router
- Vite
- Tailwind CSS
- Lucide React
- Recharts

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- SQLite for local development
- JWT-based authentication

### Machine Learning

- Python
- NumPy
- Pandas
- Scikit-learn
- Logistic Regression
- Preprocessing pipeline
- Selected-feature inference
- Probability prediction
- Risk scoring and explanation layer

### Dataset

- IEEE-CIS Fraud Detection Dataset

### Development

- Git
- GitHub
- Python virtual environment
- npm
- REST API architecture

## Project Structure

```text
razpay/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── ml/
│   │   └── main.py
│   ├── models/
│   │   ├── fraud_model.pkl
│   │   ├── preprocessor.pkl
│   │   ├── selected_features.json
│   │   └── model_metadata.json
│   ├── scripts/
│   │   └── seed_demo_data.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
├── ieee-fraud-detection/
│   ├── train_transaction.csv
│   ├── train_identity.csv
│   ├── test_transaction.csv
│   ├── test_identity.csv
│   └── sample_submission.csv
└── README.md
```

The full IEEE-CIS dataset should remain local and should not be committed to GitHub.

## How to Run Locally

### Prerequisites

Install:

- Python 3.10 or newer
- Node.js and npm
- Git
- IEEE-CIS Fraud Detection dataset if you want to populate the dashboard with real demo transactions

### 1. Clone the Repository

```bash
git clone https://github.com/ChristyFrancis99/razpay.git
cd razpay
```

### 2. Set Up the Backend

Open PowerShell in the backend directory:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Verify Model Artifacts

Make sure these files exist in `backend/models/`:

```text
fraud_model.pkl
preprocessor.pkl
selected_features.json
model_metadata.json
```

### 4. Add the IEEE-CIS Dataset Locally

The preferred layout is:

```text
razpay/
└── ieee-fraud-detection/
    ├── train_transaction.csv
    ├── train_identity.csv
    ├── test_transaction.csv
    └── test_identity.csv
```

The backend also supports the training files under `backend/data/`.

The large dataset is intentionally not committed to GitHub.

### 5. Start FastAPI

From the backend directory:

```powershell
uvicorn app.main:app --reload --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

### 6. Populate Demo Transactions

Keep FastAPI running and open a second PowerShell terminal:

```powershell
cd backend
.\.venv\Scripts\activate
python -m scripts.seed_demo_data
```

The seeder reads the large IEEE-CIS CSV files in chunks, selects representative transactions, runs them through the same inference pipeline used by the application, and persists the scored results in the local database.

To clear the local scored transactions and create a fresh demo dataset:

```powershell
python -m scripts.seed_demo_data --clear
```

Use `--clear` only for a local demonstration database because it removes existing scored transactions.

### 7. Start the Frontend

Open a third terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

### 8. Test the Main Workflow

After the backend and frontend are running and demo transactions have been seeded:

```text
Overview
   ↓
Transactions
   ↓
Select a suspicious transaction
   ↓
Investigation
   ↓
Review risk score, probability, factors and explanation
   ↓
Choose ALLOW / REVIEW / HOLD
   ↓
Audit Trail
```

Also test:

- Merchants
- Copilot
- System Health
- Users & Roles

## Local Development Commands

### Terminal 1: Backend

```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Demo Data

```powershell
cd backend
.\.venv\Scripts\activate
python -m scripts.seed_demo_data
```

### Terminal 3: Frontend

```powershell
cd frontend
npm run dev
```

## API Overview

The backend provides API groups for:

```text
/auth
/transactions
/merchants
/risk
/copilot
/analytics
/audit
/cases
```

Health endpoints:

```text
GET /api/health
GET /api/health/ready
```

The transaction prediction workflow uses the trained ML model and persists scored transactions for use by the dashboard.

## Data and Security Considerations

The IEEE-CIS dataset is large and should not be committed to the public repository. Keep it in a local directory and rely on the repository's ignore rules to prevent accidental commits.

For production deployment, use secure secrets management, a production database, restricted CORS origins, secure authentication configuration, appropriate logging and monitoring, and the required financial-data privacy and compliance controls.

## Project Goal

The goal of Razorpay Risk Intelligence is to demonstrate how machine-learning based fraud detection can be transformed into an operational risk-intelligence workflow where predictions are explainable, investigators remain involved in important decisions, merchant risk can be investigated, and actions are recorded in an auditable system.
