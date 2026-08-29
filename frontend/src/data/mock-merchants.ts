import type { Merchant, GraphNode, GraphEdge } from "@/types/merchant";
import { riskLevelFromScore } from "@/types/risk";

function buildGraph(name: string): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = [
    { id: "m", label: name, type: "merchant", x: 50, y: 50, risk: "HIGH" },
    { id: "c1", label: "CUS-40218", type: "customer", x: 18, y: 20, risk: "CRITICAL" },
    { id: "c2", label: "CUS-41892", type: "customer", x: 16, y: 62, risk: "MEDIUM" },
    { id: "c3", label: "CUS-42714", type: "customer", x: 26, y: 86, risk: "HIGH" },
    { id: "t1", label: "TXN-92831", type: "transaction", x: 52, y: 14, risk: "CRITICAL" },
    { id: "t2", label: "TXN-90447", type: "transaction", x: 78, y: 26, risk: "HIGH" },
    { id: "t3", label: "TXN-90912", type: "transaction", x: 82, y: 62, risk: "MEDIUM" },
    { id: "d1", label: "DEV-8831", type: "device", x: 60, y: 86, risk: "CRITICAL" },
    { id: "d2", label: "DEV-4407", type: "device", x: 88, y: 88, risk: "MEDIUM" },
    { id: "l1", label: "Mumbai, IN", type: "location", x: 34, y: 44 },
    { id: "l2", label: "Lagos, NG", type: "location", x: 66, y: 44, risk: "HIGH" },
  ];
  const edges: GraphEdge[] = [
    { from: "m", to: "t1", suspicious: true },
    { from: "m", to: "t2", suspicious: true },
    { from: "m", to: "t3" },
    { from: "c1", to: "t1", suspicious: true },
    { from: "c2", to: "t3" },
    { from: "c3", to: "t2", suspicious: true },
    { from: "d1", to: "c1", suspicious: true },
    { from: "d1", to: "c3", suspicious: true },
    { from: "d2", to: "c2" },
    { from: "m", to: "l1" },
    { from: "m", to: "l2", suspicious: true },
    { from: "c1", to: "l2", suspicious: true },
  ];
  return { nodes, edges };
}

function trend(base: number, growth: number) {
  const months = ["Mar", "Apr", "May", "Jun", "Jul", "Aug"];
  return months.map((month, i) => ({
    month,
    fraudRate: Number((base + growth * i + (i % 2 === 0 ? 0.08 : -0.05)).toFixed(2)),
    volume: Math.round(1_800_000 + i * 240_000 + (i % 3) * 130_000),
  }));
}

const raw: Array<Partial<Merchant> & Pick<Merchant, "id" | "name" | "category" | "riskScore">> = [
  {
    id: "MRC-1001",
    name: "Nova Electronics",
    category: "Electronics",
    riskScore: 78,
    country: "India",
    accountAge: "1 yr 2 mo",
    transactions: 184_920,
    volume: 412_800_000,
    fraudRate: 3.8,
    chargebackRate: 2.4,
    customerCount: 61_420,
    status: "Investigation",
  },
  { id: "MRC-1008", name: "CryptoBridge Exchange", category: "Crypto", riskScore: 91, country: "Singapore", accountAge: "7 mo", transactions: 62_310, volume: 988_400_000, fraudRate: 6.2, chargebackRate: 4.1, customerCount: 21_800, status: "Escalated" },
  { id: "MRC-1006", name: "Lumen Digital Goods", category: "Digital Goods", riskScore: 72, country: "United Kingdom", accountAge: "2 yr 4 mo", transactions: 220_140, volume: 96_200_000, fraudRate: 2.9, chargebackRate: 1.8, customerCount: 88_030, status: "Monitoring" },
  { id: "MRC-1007", name: "Meridian Jewels", category: "Luxury Retail", riskScore: 66, country: "UAE", accountAge: "3 yr 1 mo", transactions: 18_740, volume: 640_900_000, fraudRate: 1.9, chargebackRate: 1.2, customerCount: 9_310, status: "Monitoring" },
  { id: "MRC-1003", name: "SkyRoute Travel", category: "Travel", riskScore: 54, country: "India", accountAge: "5 yr 6 mo", transactions: 402_880, volume: 1_240_000_000, fraudRate: 0.9, chargebackRate: 0.7, customerCount: 190_220, status: "Active" },
  { id: "MRC-1010", name: "BlueCart Fashion", category: "Apparel", riskScore: 41, country: "India", accountAge: "4 yr", transactions: 810_400, volume: 520_100_000, fraudRate: 0.6, chargebackRate: 0.5, customerCount: 402_700, status: "Active" },
  { id: "MRC-1002", name: "Amazon India", category: "Marketplace", riskScore: 22, country: "India", accountAge: "9 yr 3 mo", transactions: 4_920_100, volume: 18_400_000_000, fraudRate: 0.2, chargebackRate: 0.2, customerCount: 2_910_000, status: "Active" },
  { id: "MRC-1004", name: "Urban Grocers", category: "Grocery", riskScore: 18, country: "India", accountAge: "6 yr", transactions: 1_402_600, volume: 388_000_000, fraudRate: 0.1, chargebackRate: 0.1, customerCount: 620_400, status: "Active" },
  { id: "MRC-1005", name: "Peak Fitness", category: "Health & Fitness", riskScore: 34, country: "India", accountAge: "2 yr 9 mo", transactions: 96_200, volume: 42_600_000, fraudRate: 0.4, chargebackRate: 0.3, customerCount: 38_100, status: "Active" },
  { id: "MRC-1009", name: "Zenith Fuel", category: "Fuel", riskScore: 62, country: "Nigeria", accountAge: "11 mo", transactions: 74_300, volume: 61_500_000, fraudRate: 2.2, chargebackRate: 1.6, customerCount: 28_900, status: "Investigation" },
];

export const mockMerchants: Merchant[] = raw.map((m) => {
  const riskLevel = riskLevelFromScore(m.riskScore);
  const high = m.riskScore >= 61;
  return {
    country: "India",
    accountAge: "2 yr",
    transactions: 100_000,
    volume: 100_000_000,
    fraudRate: 1,
    chargebackRate: 0.8,
    customerCount: 40_000,
    status: "Active",
    ...m,
    riskLevel,
    averageTransaction: Math.round((m.volume ?? 100_000_000) / (m.transactions ?? 100_000)),
    signals: [
      { label: "High fraud concentration", severity: high ? "CRITICAL" : "LOW", detail: `${m.fraudRate}% fraud rate against a ${high ? "0.6" : "0.8"}% category baseline.` },
      { label: "Unusual transaction velocity", severity: high ? "HIGH" : "LOW", detail: high ? "Authorisation volume up 214% week-over-week without seasonal driver." : "Velocity stable across the trailing 8 weeks." },
      { label: "Abnormal amount distribution", severity: high ? "HIGH" : "MEDIUM", detail: high ? "Bimodal ticket distribution with a synthetic cluster near the 3DS exemption limit." : "Amount distribution within expected category shape." },
      { label: "Multiple suspicious devices", severity: high ? "CRITICAL" : "LOW", detail: high ? "11 device fingerprints shared across 43 customer accounts." : "No shared-device clustering detected." },
      { label: "Geographic anomaly", severity: high ? "MEDIUM" : "LOW", detail: high ? "18% of settled volume originates outside the declared operating region." : "Traffic geography matches the registered footprint." },
    ],
    aiSummary: high
      ? `${m.name} demonstrates elevated risk due to increasing fraud concentration, abnormal transaction velocity, and repeated associations with devices involved in previously flagged activity. Exposure is concentrated in high-ticket card-not-present volume settled in the last 21 days.`
      : `${m.name} operates inside expected risk tolerances. Fraud rate, chargeback ratio and device diversity are all consistent with the ${m.category?.toLowerCase()} category baseline, and no anomalous clusters were detected in the review window.`,
    evidence: high
      ? [
          `${Math.round((m.transactions ?? 0) * ((m.fraudRate ?? 1) / 100)).toLocaleString("en-IN")} transactions confirmed fraudulent in the trailing 90 days.`,
          "11 device fingerprints shared across 43 distinct customer accounts.",
          "Chargeback ratio breached the 2% scheme threshold in 2 consecutive months.",
          "Cross-border settlement corridor overlaps two watchlisted intermediaries.",
        ]
      : [
          "Fraud and chargeback ratios below scheme monitoring thresholds.",
          "No shared-device clusters detected in the trailing 90 days.",
          "Settlement geography consistent with the registered entity.",
        ],
    recommendedAction: high
      ? "Place merchant under enhanced monitoring, hold settlement for high-ticket card-not-present volume, and request updated KYB documentation within 7 days."
      : "Maintain standard monitoring cadence. No intervention required this cycle.",
    trend: trend(high ? 1.6 : 0.2, high ? 0.45 : 0.05),
    graph: buildGraph(m.name),
  } as Merchant;
});

export function getMerchantByIdOrName(idOrName: string): Merchant | undefined {
  return mockMerchants.find(
    (m) => m.id.toLowerCase() === idOrName.toLowerCase() || m.name.toLowerCase() === idOrName.toLowerCase(),
  );
}
