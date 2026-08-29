import type { RiskLevel } from "./risk";

export type MerchantStatus = "Active" | "Monitoring" | "Investigation" | "Escalated" | "Suspended";

export interface MerchantSignal {
  label: string;
  severity: RiskLevel;
  detail: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "merchant" | "customer" | "transaction" | "device" | "location";
  x: number;
  y: number;
  risk?: RiskLevel;
}

export interface GraphEdge {
  from: string;
  to: string;
  suspicious?: boolean;
}

export interface Merchant {
  id: string;
  name: string;
  category: string;
  country: string;
  accountAge: string;
  transactions: number;
  volume: number;
  averageTransaction: number;
  fraudRate: number;
  chargebackRate: number;
  customerCount: number;
  riskScore: number;
  riskLevel: RiskLevel;
  status: MerchantStatus;
  signals: MerchantSignal[];
  aiSummary: string;
  evidence: string[];
  recommendedAction: string;
  trend: { month: string; fraudRate: number; volume: number }[];
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
}
