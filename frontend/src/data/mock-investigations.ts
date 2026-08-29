import type { Investigation, RiskDecisionRecord, Alert } from "@/types/investigation";

export const mockInvestigations: Investigation[] = [
  { id: "INV-2201", transactionId: "TXN-92831", riskScore: 87, reason: "Device linked to 6 accounts · amount 4.2x baseline", analyst: "P. Raghavan", ageMinutes: 12, status: "Investigating", priority: "P1" },
  { id: "INV-2202", transactionId: "TXN-90042", riskScore: 94, reason: "Card testing sequence on crypto off-ramp", analyst: "S. Menon", ageMinutes: 27, status: "Escalated", priority: "P1" },
  { id: "INV-2203", transactionId: "TXN-90019", riskScore: 81, reason: "Cross-border corridor with sanctions proximity", analyst: "Unassigned", ageMinutes: 44, status: "New", priority: "P2" },
  { id: "INV-2204", transactionId: "TXN-90066", riskScore: 76, reason: "Velocity spike 280% against rolling baseline", analyst: "A. Deshmukh", ageMinutes: 68, status: "Investigating", priority: "P2" },
  { id: "INV-2205", transactionId: "TXN-90031", riskScore: 72, reason: "Merchant fraud concentration above category baseline", analyst: "P. Raghavan", ageMinutes: 96, status: "Investigating", priority: "P2" },
  { id: "INV-2206", transactionId: "TXN-90008", riskScore: 69, reason: "Geo mismatch with last trusted session", analyst: "Unassigned", ageMinutes: 133, status: "New", priority: "P3" },
  { id: "INV-2207", transactionId: "TXN-90054", riskScore: 65, reason: "Chargeback history on funding instrument", analyst: "S. Menon", ageMinutes: 210, status: "Resolved", priority: "P3" },
];

export const mockDecisions: RiskDecisionRecord[] = [
  { id: "DEC-8801", transactionId: "TXN-92831", riskScore: 87, aiRecommendation: "REVIEW", analystDecision: "HOLD", decisionTime: "2026-08-29 14:32", analyst: "P. Raghavan", reason: "Device reuse confirmed across 6 accounts; funds held pending customer callback." },
  { id: "DEC-8802", transactionId: "TXN-90042", riskScore: 94, aiRecommendation: "HOLD", analystDecision: "HOLD", decisionTime: "2026-08-29 13:58", analyst: "S. Menon", reason: "Card testing pattern verified against issuer decline stream." },
  { id: "DEC-8803", transactionId: "TXN-90011", riskScore: 44, aiRecommendation: "ALLOW", analystDecision: "ALLOW", decisionTime: "2026-08-29 13:41", analyst: "Auto (Policy v4.2)", reason: "Within customer behavioural envelope; no anomaly triggered." },
  { id: "DEC-8804", transactionId: "TXN-90066", riskScore: 76, aiRecommendation: "REVIEW", analystDecision: "REVIEW", decisionTime: "2026-08-29 12:20", analyst: "A. Deshmukh", reason: "Awaiting merchant confirmation of fulfilment address change." },
  { id: "DEC-8805", transactionId: "TXN-90005", riskScore: 63, aiRecommendation: "REVIEW", analystDecision: "ALLOW", decisionTime: "2026-08-29 11:47", analyst: "P. Raghavan", reason: "Customer verified via step-up authentication; travel notice on file." },
  { id: "DEC-8806", transactionId: "TXN-90019", riskScore: 81, aiRecommendation: "HOLD", analystDecision: "REVIEW", decisionTime: "2026-08-29 10:36", analyst: "S. Menon", reason: "Corridor risk noted but counterparty is an existing verified beneficiary." },
  { id: "DEC-8807", transactionId: "TXN-90023", riskScore: 28, aiRecommendation: "ALLOW", analystDecision: "ALLOW", decisionTime: "2026-08-29 09:52", analyst: "Auto (Policy v4.2)", reason: "Low-risk recurring grocery spend." },
  { id: "DEC-8808", transactionId: "TXN-90071", riskScore: 90, aiRecommendation: "HOLD", analystDecision: "HOLD", decisionTime: "2026-08-28 22:14", analyst: "A. Deshmukh", reason: "Synthetic identity indicators on the originating account." },
];

export const mockAlerts: Alert[] = [
  { id: "ALT-5501", type: "Critical Fraud", severity: "CRITICAL", title: "Confirmed fraud ring activity", detail: "9 transactions across 4 accounts share a single device fingerprint (DEV-8831).", entity: "DEV-8831", time: "2026-08-29 14:41", status: "Open" },
  { id: "ALT-5502", type: "Merchant Risk", severity: "HIGH", title: "Merchant chargeback threshold breached", detail: "CryptoBridge Exchange exceeded the 2% scheme chargeback ratio for a second month.", entity: "MRC-1008", time: "2026-08-29 13:12", status: "Acknowledged" },
  { id: "ALT-5503", type: "Transaction Anomaly", severity: "HIGH", title: "Velocity spike detected", detail: "Customer CUS-40218 initiated 7 authorisations in 9 minutes.", entity: "CUS-40218", time: "2026-08-29 12:04", status: "Open" },
  { id: "ALT-5504", type: "System Alert", severity: "MEDIUM", title: "Scoring latency elevated", detail: "p99 scoring latency rose to 214 ms (baseline 90 ms) on the risk engine.", entity: "risk-engine-02", time: "2026-08-29 11:20", status: "Acknowledged" },
  { id: "ALT-5505", type: "Merchant Risk", severity: "MEDIUM", title: "Unusual settlement geography", detail: "18% of Zenith Fuel volume settled outside the declared operating region.", entity: "MRC-1009", time: "2026-08-29 10:02", status: "Open" },
  { id: "ALT-5506", type: "Transaction Anomaly", severity: "LOW", title: "Amount distribution shift", detail: "Lumen Digital Goods shows clustering near the 3DS exemption limit.", entity: "MRC-1006", time: "2026-08-29 08:36", status: "Resolved" },
  { id: "ALT-5507", type: "Critical Fraud", severity: "CRITICAL", title: "Sanctioned counterparty proximity", detail: "Wire transfer TXN-90019 routed via a watchlisted intermediary bank.", entity: "TXN-90019", time: "2026-08-28 21:44", status: "Open" },
  { id: "ALT-5508", type: "System Alert", severity: "LOW", title: "Model drift within tolerance", detail: "Population stability index at 0.11 for feature set v4.2.", entity: "model-v4.2", time: "2026-08-28 19:10", status: "Resolved" },
];
