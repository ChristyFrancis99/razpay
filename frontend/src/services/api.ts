/**
 * API service layer.
 *
 * Every function here currently resolves mock data after a small simulated
 * latency. To connect a real backend, replace each body with a `fetch` call to
 * the endpoint listed in the JSDoc above it — signatures and return types stay
 * identical, so no UI code needs to change.
 */
import { mockTransactions } from "@/data/mock-transactions";
import { mockMerchants } from "@/data/mock-merchants";
import { mockInvestigations, mockDecisions, mockAlerts } from "@/data/mock-investigations";
import { mockAuditLogs } from "@/data/mock-audit-logs";
import { mockAnalytics, type AnalyticsPayload } from "@/data/mock-analytics";
import type { Transaction } from "@/types/transaction";
import type { Merchant } from "@/types/merchant";
import type { Alert, Investigation, RiskDecisionRecord } from "@/types/investigation";
import type { AuditLogEntry } from "@/types/audit";
import type { Decision } from "@/types/risk";

export const API_BASE_URL = import.meta.env["VITE_API_BASE_URL"] ?? "/api";

const latency = (ms = 320) => new Promise((resolve) => setTimeout(resolve, ms));

export interface TransactionQuery {
  search?: string;
  riskLevel?: string;
  decision?: string;
  paymentMethod?: string;
  country?: string;
  status?: string;
  minAmount?: number;
  page?: number;
  pageSize?: number;
}

/** GET /transactions */
export async function getTransactions(query: TransactionQuery = {}) {
  await latency();
  const {
    search = "",
    riskLevel = "all",
    decision = "all",
    paymentMethod = "all",
    country = "all",
    status = "all",
    minAmount = 0,
    page = 1,
    pageSize = 12,
  } = query;

  const term = search.trim().toLowerCase();
  const filtered = mockTransactions.filter((t) => {
    if (term && ![t.id, t.merchant, t.customer, t.customerId].some((v) => v.toLowerCase().includes(term))) return false;
    if (riskLevel !== "all" && t.riskLevel !== riskLevel) return false;
    if (decision !== "all" && t.decision !== decision) return false;
    if (paymentMethod !== "all" && t.paymentMethod !== paymentMethod) return false;
    if (country !== "all" && t.country !== country) return false;
    if (status !== "all" && t.investigationStatus !== status) return false;
    if (t.amount < minAmount) return false;
    return true;
  });

  const start = (page - 1) * pageSize;
  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
  };
}

/** GET /transactions/:id */
export async function getTransaction(id: string): Promise<Transaction | undefined> {
  await latency(220);
  return mockTransactions.find((t) => t.id.toLowerCase() === id.toLowerCase());
}

/** GET /transactions/live */
export async function getLiveTransactions(limit = 8): Promise<Transaction[]> {
  await latency(180);
  return mockTransactions.slice(0, limit);
}

/** GET /merchants */
export async function getMerchants(): Promise<Merchant[]> {
  await latency();
  return mockMerchants;
}

/** GET /merchants/:id */
export async function getMerchant(id: string): Promise<Merchant | undefined> {
  await latency(220);
  return mockMerchants.find((m) => m.id.toLowerCase() === id.toLowerCase());
}

/** GET /investigations */
export async function getInvestigations(): Promise<Investigation[]> {
  await latency(200);
  return mockInvestigations;
}

/** GET /decisions */
export async function getRiskDecisions(): Promise<RiskDecisionRecord[]> {
  await latency();
  return mockDecisions;
}

/** GET /decisions/:id */
export async function getRiskDecision(id: string): Promise<RiskDecisionRecord | undefined> {
  await latency(180);
  return mockDecisions.find((d) => d.id === id || d.transactionId === id);
}

/** POST /transactions/:id/decision */
export async function submitDecision(input: {
  transactionId: string;
  decision: Decision;
  notes: string;
}): Promise<{ ok: true; auditId: string }> {
  await latency(500);
  return { ok: true, auditId: `AUD-${Math.floor(9000 + Math.random() * 999)}` };
}

/** GET /analytics */
export async function getAnalytics(): Promise<AnalyticsPayload> {
  await latency();
  return mockAnalytics;
}

/** GET /audit-logs */
export async function getAuditLogs(): Promise<AuditLogEntry[]> {
  await latency();
  return mockAuditLogs;
}

/** GET /alerts */
export async function getAlerts(): Promise<Alert[]> {
  await latency();
  return mockAlerts;
}

export interface CopilotResponse {
  summary: string;
  riskScore?: number;
  decision?: Decision;
  findings: string[];
  recommendedAction?: Decision;
  sources: string[];
}

/** POST /copilot/messages */
export async function sendCopilotMessage(message: string): Promise<CopilotResponse> {
  await latency(900);
  const text = message.toLowerCase();

  if (text.includes("merchant") || text.includes("nova")) {
    return {
      summary:
        "Nova Electronics shows a rising fraud concentration driven by shared-device activity and high-ticket card-not-present volume settled in the last 21 days.",
      riskScore: 78,
      decision: "REVIEW",
      findings: [
        "Fraud rate 3.8% against a 0.6% category baseline",
        "11 device fingerprints shared across 43 customer accounts",
        "Chargeback ratio breached 2% for two consecutive months",
        "18% of settled volume originates outside the declared region",
      ],
      recommendedAction: "REVIEW",
      sources: ["Merchant history", "Device signals", "Settlement ledger", "Risk model"],
    };
  }

  if (text.includes("compare") || text.includes("previous")) {
    return {
      summary:
        "Compared against the customer's trailing 90 days, this transaction is an outlier on amount and velocity but consistent on merchant category and payment instrument.",
      riskScore: 87,
      decision: "REVIEW",
      findings: [
        "Amount ₹42,500 vs. average ₹10,120 (4.2x)",
        "Velocity up 280% versus the 30-day rolling baseline",
        "Same card used in 82% of prior transactions",
        "First session from this device fingerprint",
      ],
      recommendedAction: "REVIEW",
      sources: ["Transaction history", "Customer profile", "Device signals"],
    };
  }

  if (text.includes("factor") || text.includes("signal")) {
    return {
      summary: "The strongest contributors to the current score are amount deviation and device reuse.",
      riskScore: 87,
      findings: [
        "Unusual transaction amount +32",
        "Device associated with multiple accounts +21",
        "Abnormal transaction velocity +17",
        "Location mismatch +11",
        "Previous suspicious activity +9",
      ],
      recommendedAction: "REVIEW",
      sources: ["Risk model", "Feature attribution v4.2"],
    };
  }

  return {
    summary:
      "TXN-92831 was flagged because the amount is materially above the customer's historical average, the originating device is linked to multiple accounts, and velocity sits inside a known high-risk behavioural pattern.",
    riskScore: 87,
    decision: "REVIEW",
    findings: [
      "Amount is 4.2× customer average",
      "Device linked to 6 accounts",
      "Transaction velocity increased 280%",
      "Merchant fraud rate is above baseline",
    ],
    recommendedAction: "REVIEW",
    sources: ["Transaction history", "Merchant history", "Device signals", "Risk model"],
  };
}
