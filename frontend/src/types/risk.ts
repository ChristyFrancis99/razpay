export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type Decision = "ALLOW" | "REVIEW" | "HOLD";

export type InvestigationStatus = "New" | "Investigating" | "Escalated" | "Resolved";

export interface RiskFactor {
  label: string;
  contribution: number;
  detail: string;
}

export interface RiskThresholds {
  low: [number, number];
  medium: [number, number];
  high: [number, number];
  critical: [number, number];
}

export function riskLevelFromScore(score: number): RiskLevel {
  if (score <= 30) return "LOW";
  if (score <= 60) return "MEDIUM";
  if (score <= 80) return "HIGH";
  return "CRITICAL";
}
