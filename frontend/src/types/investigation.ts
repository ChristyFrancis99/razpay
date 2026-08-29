import type { Decision, InvestigationStatus } from "./risk";

export interface Investigation {
  id: string;
  transactionId: string;
  riskScore: number;
  reason: string;
  analyst: string;
  ageMinutes: number;
  status: InvestigationStatus;
  priority: "P1" | "P2" | "P3";
}

export interface RiskDecisionRecord {
  id: string;
  transactionId: string;
  riskScore: number;
  aiRecommendation: Decision;
  analystDecision: Decision;
  decisionTime: string;
  analyst: string;
  reason: string;
}

export type AlertType = "Critical Fraud" | "Merchant Risk" | "Transaction Anomaly" | "System Alert";

export interface Alert {
  id: string;
  type: AlertType;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  title: string;
  detail: string;
  entity: string;
  time: string;
  status: "Open" | "Acknowledged" | "Resolved";
}
