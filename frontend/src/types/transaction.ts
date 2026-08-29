import type { Decision, InvestigationStatus, RiskFactor, RiskLevel } from "./risk";

export type PaymentMethod =
  | "Credit Card"
  | "Debit Card"
  | "UPI"
  | "Net Banking"
  | "Wallet"
  | "Wire Transfer";

export interface TransactionTimelineEvent {
  label: string;
  time: string;
  detail: string;
  kind: "session" | "device" | "transaction" | "engine" | "ai" | "decision";
}

export interface RelatedTransaction {
  id: string;
  date: string;
  amount: number;
  merchant: string;
  riskScore: number;
  decision: Decision;
}

export interface Transaction {
  id: string;
  timestamp: string;
  amount: number;
  currency: "INR";
  merchant: string;
  merchantId: string;
  customer: string;
  customerId: string;
  paymentMethod: PaymentMethod;
  country: string;
  location: string;
  device: string;
  ip: string;
  riskScore: number;
  riskLevel: RiskLevel;
  aiRecommendation: Decision;
  decision: Decision;
  investigationStatus: InvestigationStatus;
  explanation: string;
  riskFactors: RiskFactor[];
  timeline: TransactionTimelineEvent[];
  related: RelatedTransaction[];
}
