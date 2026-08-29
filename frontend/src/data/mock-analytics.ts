export interface AnalyticsPayload {
  kpis: { label: string; value: string; delta: number; hint: string }[];
  riskDistribution: { name: string; value: number }[];
  riskTrend: { day: string; low: number; medium: number; high: number; critical: number }[];
  fraudRateTrend: { month: string; fraudRate: number; baseline: number }[];
  transactionVolume: { month: string; volume: number; flagged: number }[];
  decisionDistribution: { name: string; value: number }[];
  fraudByCategory: { category: string; fraudRate: number }[];
  fraudByPaymentMethod: { method: string; fraudRate: number }[];
  topRiskSignals: { signal: string; frequency: number }[];
  modelMetrics: { label: string; value: number; description: string }[];
  confusionMatrix: { truePositive: number; falsePositive: number; falseNegative: number; trueNegative: number };
}

export const mockAnalytics: AnalyticsPayload = {
  kpis: [
    { label: "Transactions Monitored", value: "1,284,392", delta: 12.4, hint: "Last 30 days" },
    { label: "Suspicious Transactions", value: "3,842", delta: -3.2, hint: "Flagged by risk engine" },
    { label: "High Risk Transactions", value: "428", delta: 8.1, hint: "Score above 60" },
    { label: "Fraud Prevented", value: "₹2.4 Cr", delta: 18.6, hint: "Blocked exposure" },
  ],
  riskDistribution: [
    { name: "LOW", value: 71 },
    { name: "MEDIUM", value: 19 },
    { name: "HIGH", value: 7 },
    { name: "CRITICAL", value: 3 },
  ],
  riskTrend: [
    { day: "Aug 23", low: 41200, medium: 8100, high: 1220, critical: 310 },
    { day: "Aug 24", low: 39800, medium: 8600, high: 1340, critical: 288 },
    { day: "Aug 25", low: 44100, medium: 9200, high: 1510, critical: 402 },
    { day: "Aug 26", low: 46700, medium: 8800, high: 1420, critical: 366 },
    { day: "Aug 27", low: 45200, medium: 9700, high: 1680, critical: 441 },
    { day: "Aug 28", low: 48800, medium: 10400, high: 1790, critical: 512 },
    { day: "Aug 29", low: 47100, medium: 9900, high: 1620, critical: 468 },
  ],
  fraudRateTrend: [
    { month: "Mar", fraudRate: 0.82, baseline: 0.75 },
    { month: "Apr", fraudRate: 0.91, baseline: 0.75 },
    { month: "May", fraudRate: 0.74, baseline: 0.75 },
    { month: "Jun", fraudRate: 1.12, baseline: 0.75 },
    { month: "Jul", fraudRate: 1.34, baseline: 0.75 },
    { month: "Aug", fraudRate: 1.08, baseline: 0.75 },
  ],
  transactionVolume: [
    { month: "Mar", volume: 962_000, flagged: 2_810 },
    { month: "Apr", volume: 1_014_000, flagged: 3_120 },
    { month: "May", volume: 1_088_000, flagged: 2_940 },
    { month: "Jun", volume: 1_142_000, flagged: 3_610 },
    { month: "Jul", volume: 1_221_000, flagged: 4_080 },
    { month: "Aug", volume: 1_284_392, flagged: 3_842 },
  ],
  decisionDistribution: [
    { name: "ALLOW", value: 89 },
    { name: "REVIEW", value: 8 },
    { name: "HOLD", value: 3 },
  ],
  fraudByCategory: [
    { category: "Crypto", fraudRate: 6.2 },
    { category: "Electronics", fraudRate: 3.8 },
    { category: "Digital Goods", fraudRate: 2.9 },
    { category: "Fuel", fraudRate: 2.2 },
    { category: "Luxury Retail", fraudRate: 1.9 },
    { category: "Travel", fraudRate: 0.9 },
    { category: "Apparel", fraudRate: 0.6 },
    { category: "Grocery", fraudRate: 0.1 },
  ],
  fraudByPaymentMethod: [
    { method: "Wire Transfer", fraudRate: 4.4 },
    { method: "Credit Card", fraudRate: 2.8 },
    { method: "Wallet", fraudRate: 1.7 },
    { method: "Debit Card", fraudRate: 1.1 },
    { method: "Net Banking", fraudRate: 0.7 },
    { method: "UPI", fraudRate: 0.4 },
  ],
  topRiskSignals: [
    { signal: "Device shared across accounts", frequency: 1_284 },
    { signal: "Amount above customer baseline", frequency: 1_106 },
    { signal: "Velocity spike", frequency: 902 },
    { signal: "Geo / IP mismatch", frequency: 744 },
    { signal: "Card testing sequence", frequency: 512 },
    { signal: "Merchant fraud concentration", frequency: 388 },
  ],
  modelMetrics: [
    { label: "Accuracy", value: 0.972, description: "Overall correct classifications" },
    { label: "Precision", value: 0.914, description: "Flagged transactions that were truly fraudulent" },
    { label: "Recall", value: 0.887, description: "Fraudulent transactions successfully caught" },
    { label: "F1 Score", value: 0.9, description: "Harmonic mean of precision and recall" },
    { label: "ROC-AUC", value: 0.961, description: "Separability across all thresholds" },
  ],
  confusionMatrix: {
    truePositive: 3_412,
    falsePositive: 321,
    falseNegative: 434,
    trueNegative: 1_280_225,
  },
};

export const systemStatus = [
  { label: "AI Engine", state: "Operational" as const, detail: "Model v4.2 · p99 96 ms" },
  { label: "Transaction Monitoring", state: "Operational" as const, detail: "1.2M events/day" },
  { label: "Risk Engine", state: "Operational" as const, detail: "Realtime scoring" },
];
