# Risk Sentinel

BUILD THE COMPLETE FRONTEND — RISK INTELLIGENCE PLATFORM

You are a senior product designer and frontend engineer.

Build a complete, production-quality frontend for a fintech/cybersecurity product called:

Risk Intelligence Platform

The platform is an AI-powered risk investigation system for financial transactions.

The core product concept is:

AI Risk Manager

It investigates transactions, identifies suspicious behaviour, explains why a transaction is risky, investigates merchant-level patterns, and produces a final risk decision.

The three major product capabilities are:

Explainable Fraud Agent

Merchant Risk Investigator

Real-time Transaction Copilot

The final decision should be:

ALLOW / REVIEW / HOLD

with a complete audit trail.

IMPORTANT

This is a FRONTEND-ONLY task.

Do NOT implement the machine learning model, database, fraud detection algorithm, authentication backend, or API server.

Use realistic mock data and create a clean API/service layer so the real backend can be connected later.

The frontend must look like a serious fintech/security product rather than a generic admin dashboard.

TECH STACK

Use:

React

TypeScript

Tailwind CSS

shadcn/ui

Recharts

Lucide React icons

React Router if routing is required

If the existing project already has a framework/configuration, preserve it.

Do NOT migrate the project to Next.js if it is already using another React framework.

Keep the implementation modular and production-quality.

DESIGN DIRECTION

Create a premium institutional fintech/security interface.

Visual references:

modern banking dashboards

fraud investigation platforms

cybersecurity SOC interfaces

enterprise risk management software

premium AI SaaS products

The design should feel:

professional

trustworthy

technical

minimal

premium

data-dense but readable

suitable for banks and financial institutions

Avoid:

excessive gradients

childish illustrations

excessive glassmorphism

huge decorative elements

generic template-dashboard appearance

excessive rounded cards everywhere

Use visual hierarchy instead of decoration.

COLOR SYSTEM

Primary visual language:

deep navy

dark blue

white

cool gray

muted purple

teal

risk colors

Risk colors:

LOW:
green

MEDIUM:
yellow/amber

HIGH:
orange

CRITICAL:
red

Use colors consistently throughout the application.

GLOBAL LAYOUT

Create:

Sidebar
+
Top navigation
+
Main content area

Sidebar navigation:

Dashboard
Investigations
Transactions
Merchants
Risk Decisions
Analytics
Audit Logs
Alerts

Bottom sidebar:

Settings
Help
User profile

Top bar:

Global search
Notifications
System status
User profile

PAGE 1 — LOGIN

Route:

/login

Create a premium login screen.

Content:

Risk Intelligence Platform

"AI-powered transaction and merchant risk intelligence."

Fields:

Email
Password

Buttons:

Sign In
Continue with Google

Include:

Remember me
Forgot password

Also include:

"Secure enterprise access"

Do not implement real authentication.

Use mock login behaviour.

After login:

redirect to /dashboard

PAGE 2 — MAIN DASHBOARD

Route:

/dashboard

This is the main command center.

Header:

Good morning, Analyst

"Here's your current risk overview."

Show system status:

AI Engine: Operational
Transaction Monitoring: Operational
Risk Engine: Operational

KPI CARDS

Create:

Transactions Monitored

Suspicious Transactions

High Risk Transactions

Fraud Prevented

Example:

Transactions Monitored
1,284,392

Suspicious Transactions
3,842

High Risk
428

Fraud Prevented
₹2.4 Cr

Use subtle trend indicators.

Example:

+12.4%
-3.2%

RISK OVERVIEW

Create a large analytics section.

Charts:

Risk Distribution

Low
Medium
High
Critical

Use a donut/pie chart.

Also create:

Risk Trend

with time-series chart.

LIVE TRANSACTION FEED

Create a live-looking transaction table.

Columns:

Transaction ID
Time
Amount
Merchant
Customer
Risk Score
Decision
Status

Example:

TXN-92831
₹42,500
Amazon
82
REVIEW

Use realistic data.

Rows should be clickable.

Clicking a transaction opens:

/transactions/:id

INVESTIGATION QUEUE

Create a section:

Priority Investigations

Each investigation should display:

Transaction
Risk Score
Reason
Assigned Analyst
Age
Status

Statuses:

New
Investigating
Escalated
Resolved

PAGE 3 — TRANSACTIONS

Route:

/transactions

Create a professional transaction investigation table.

Filters:

Risk Level
Decision
Amount
Date
Merchant
Payment Method
Country
Status

Search:

Transaction ID
Merchant
Customer

Columns:

Transaction ID
Timestamp
Amount
Merchant
Payment Method
Risk Score
Risk Level
Decision
Investigation Status

Add pagination.

PAGE 4 — TRANSACTION INVESTIGATION

Route:

/transactions/:id

This is one of the most important pages.

Create a complete investigation workspace.

Header:

Transaction TXN-92831

Risk Score:

87 / 100

Risk Level:

HIGH

Decision:

REVIEW

TRANSACTION SUMMARY

Display:

Amount
Timestamp
Merchant
Payment Method
Device
IP
Location
Customer

AI EXPLANATION

Create a large section:

Why was this transaction flagged?

Example:

"This transaction was flagged because the transaction amount is significantly higher than the customer's historical average, the device has appeared across multiple accounts, and the transaction occurs within a high-risk behavioural pattern."

Do not make explanations overly verbose.

RISK FACTORS

Create ranked factors:

Unusual transaction amount +32

Device associated with multiple accounts +21

Abnormal transaction velocity +17

Location mismatch +11

Previous suspicious activity +9

Use horizontal contribution bars.

TRANSACTION TIMELINE

Show:

Login
Device detected
Transaction initiated
Risk engine triggered
AI investigation
Decision

Use a vertical timeline.

RELATED TRANSACTIONS

Display previous transactions from the same customer/device/card.

Columns:

Date
Amount
Merchant
Risk
Decision

DECISION PANEL

Create a highly visible decision card.

Current recommendation:

REVIEW

Buttons:

ALLOW
REVIEW
HOLD

When clicked, show confirmation modal.

Also include:

Analyst Notes

textarea

Button:

Save Decision

PAGE 5 — MERCHANTS

Route:

/merchants

Create merchant risk intelligence page.

KPIs:

Total Merchants
High Risk Merchants
Under Investigation
Recently Escalated

Merchant table:

Merchant
Category
Transactions
Volume
Fraud Rate
Risk Score
Risk Level
Status

Example:

Merchant:
Nova Electronics

Risk Score:
78

Fraud Rate:
3.8%

Status:
Investigation

PAGE 6 — MERCHANT INVESTIGATION

Route:

/merchants/:id

This should feel like an investigation platform.

Header:

Nova Electronics

Risk Score:

78 / 100

Risk Level:

HIGH

MERCHANT PROFILE

Show:

Merchant ID
Category
Country
Account Age
Transaction Volume
Average Transaction
Chargeback/Fraud Rate
Customer Count

MERCHANT RISK SIGNALS

Show:

High fraud concentration
Unusual transaction velocity
Abnormal transaction amount distribution
Multiple suspicious devices
Geographic anomaly

MERCHANT TRANSACTION GRAPH

Create a visual relationship graph showing:

Merchant
Customers
Transactions
Devices
Locations

Use a clean network visualization.

It does not need real graph computation.

Use mock data.

MERCHANT RISK TREND

Chart:

Fraud rate over time.

Also:

Transaction volume over time.

AI MERCHANT INVESTIGATION

Create:

AI Investigation Summary

Example:

"The merchant demonstrates elevated risk due to increasing fraud concentration, abnormal transaction velocity, and repeated associations with devices involved in previously flagged activity."

Then show:

Evidence
Risk Signals
Recommended Action

PAGE 7 — REAL-TIME TRANSACTION COPILOT

Route:

/copilot

This is the AI assistant interface.

Create a professional investigation chat.

Header:

Transaction Copilot

Subtitle:

"Investigate transactions, merchants and risk signals."

Example user questions:

"Why was TXN-92831 flagged?"

"Show suspicious activity associated with this merchant."

"What are the strongest risk factors?"

"Compare this transaction with the customer's previous activity."

COPILOT RESPONSE

Responses should contain structured information.

Example:

Risk Score:
87

Decision:
REVIEW

Key Findings:

• Amount is 4.2× customer average
• Device linked to 6 accounts
• Transaction velocity increased 280%
• Merchant fraud rate is above baseline

Recommended Action:

REVIEW

Sources:

Transaction history
Merchant history
Device signals
Risk model

PAGE 8 — RISK DECISIONS

Route:

/decisions

Create decision management interface.

Tabs:

All
Allow
Review
Hold

Table:

Transaction
Risk Score
AI Recommendation
Analyst Decision
Decision Time
Analyst
Reason

Allow/Reivew/Hold should be clearly differentiated.

PAGE 9 — ANALYTICS

Route:

/analytics

Create enterprise risk analytics dashboard.

Charts:

Fraud Rate Trend
Transaction Volume
Risk Distribution
Decision Distribution
Fraud by Merchant Category
Fraud by Payment Method
Top Risk Signals
Model Performance

Model metrics:

Accuracy
Precision
Recall
F1 Score
ROC-AUC

Also create:

Confusion Matrix

Use realistic mock values.

Clearly label mock/model metrics if appropriate.

PAGE 10 — AUDIT LOGS

Route:

/audit-logs

Create complete audit trail.

Columns:

Timestamp
Actor
Action
Entity
Previous Decision
New Decision
Reason

Example:

14:32
Analyst
Decision Updated
TXN-92831
REVIEW → HOLD

Every decision must be traceable.

PAGE 11 — ALERTS

Route:

/alerts

Create alert center.

Types:

Critical Fraud
Merchant Risk
Transaction Anomaly
System Alert

Filters:

Severity
Status
Date

PAGE 12 — SETTINGS

Route:

/settings

Sections:

Profile
Security
Notifications
Risk Thresholds
System Preferences

Risk threshold example:

LOW:
0–30

MEDIUM:
31–60

HIGH:
61–80

CRITICAL:
81–100

Allow these to be edited visually, but no real backend persistence is required.

COMPONENT ARCHITECTURE

Create reusable components:

RiskBadge
RiskScore
DecisionBadge
MetricCard
TransactionTable
MerchantTable
RiskChart
RiskFactorList
InvestigationTimeline
TransactionGraph
MerchantRiskCard
AIExplanation
CopilotMessage
DecisionPanel
AuditTimeline
EmptyState
LoadingState
ErrorState
FilterBar
SearchBar
Modal
DataTable

Do NOT duplicate UI code unnecessarily.

MOCK DATA

Create separate mock data files.

For example:

src/data/mock-transactions.ts
src/data/mock-merchants.ts
src/data/mock-investigations.ts
src/data/mock-alerts.ts
src/data/mock-audit-logs.ts
src/data/mock-analytics.ts

Create TypeScript types separately:

src/types/transaction.ts
src/types/merchant.ts
src/types/investigation.ts
src/types/risk.ts
src/types/audit.ts

API SERVICE LAYER

Even though this is frontend-only, create:

src/services/api.ts

and functions such as:

getTransactions()
getTransaction(id)
getMerchants()
getMerchant(id)
getRiskDecision(id)
getAnalytics()
getAuditLogs()
sendCopilotMessage(message)

For now these functions should return mock data.

Make the structure easy to replace with real API calls later.

UX REQUIREMENTS

The application must have:

Loading states
Empty states
Error states
Hover states
Active states
Responsive layout
Keyboard-friendly controls
Accessible buttons
Tooltips where useful
Confirmation dialogs for important decisions

Tables should be readable.

Charts should not overwhelm the interface.

IMPORTANT PRODUCT PRINCIPLE

The application should NOT feel like:

"just another analytics dashboard."

It should feel like:

"an AI-powered financial investigation workstation."

The primary user journey should be:

Dashboard
→ suspicious transaction
→ investigation
→ AI explanation
→ evidence
→ risk decision
→ audit log

Secondary journey:

Dashboard
→ merchant
→ merchant investigation
→ AI investigation
→ risk decision

Third journey:

Transaction
→ Copilot
→ ask question
→ evidence
→ recommendation

FINAL REQUIREMENT

Build the entire frontend.

Do not leave major pages as placeholders.

Do not use lorem ipsum.

Use realistic financial/security data.

Keep the UI consistent across every page.

Make the final result polished enough for:

college project demonstration

hackathon presentation

fintech prototype

investor/demo presentation

At the end, provide:

Complete folder structure

List of created files

How to run the frontend

Where mock API calls are located

Exactly which API endpoints the backend will need to implement later

Do not implement the backend in this task.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/b8fe01ba-2a06-4a26-b6b7-dc09f4c87295).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
