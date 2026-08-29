import type { PaymentMethod, Transaction } from "@/types/transaction";
import type { Decision, InvestigationStatus } from "@/types/risk";
import { riskLevelFromScore } from "@/types/risk";

const merchants = [
  { id: "MRC-1001", name: "Nova Electronics", category: "Electronics" },
  { id: "MRC-1002", name: "Amazon India", category: "Marketplace" },
  { id: "MRC-1003", name: "SkyRoute Travel", category: "Travel" },
  { id: "MRC-1004", name: "Urban Grocers", category: "Grocery" },
  { id: "MRC-1005", name: "Peak Fitness", category: "Health & Fitness" },
  { id: "MRC-1006", name: "Lumen Digital Goods", category: "Digital Goods" },
  { id: "MRC-1007", name: "Meridian Jewels", category: "Luxury Retail" },
  { id: "MRC-1008", name: "CryptoBridge Exchange", category: "Crypto" },
  { id: "MRC-1009", name: "Zenith Fuel", category: "Fuel" },
  { id: "MRC-1010", name: "BlueCart Fashion", category: "Apparel" },
];

const customers = [
  { id: "CUS-40218", name: "R. Venkatesh" },
  { id: "CUS-40551", name: "A. Kapoor" },
  { id: "CUS-41120", name: "M. Fernandes" },
  { id: "CUS-41892", name: "S. Iyer" },
  { id: "CUS-42033", name: "N. Bhattacharya" },
  { id: "CUS-42714", name: "D. Chauhan" },
  { id: "CUS-43006", name: "P. Nair" },
  { id: "CUS-43590", name: "K. Sethi" },
];

const methods: PaymentMethod[] = [
  "Credit Card",
  "Debit Card",
  "UPI",
  "Net Banking",
  "Wallet",
  "Wire Transfer",
];

const locations = [
  { city: "Mumbai, IN", country: "India" },
  { city: "Bengaluru, IN", country: "India" },
  { city: "Delhi NCR, IN", country: "India" },
  { city: "Dubai, AE", country: "UAE" },
  { city: "Singapore, SG", country: "Singapore" },
  { city: "London, GB", country: "United Kingdom" },
  { city: "Lagos, NG", country: "Nigeria" },
];

const devices = [
  "iPhone 15 · iOS 17.4",
  "Pixel 8 · Android 14",
  "Windows 11 · Chrome 126",
  "MacBook Pro · Safari 17",
  "Samsung S23 · Android 14",
  "Linux · Headless Chrome",
];

const statuses: InvestigationStatus[] = ["New", "Investigating", "Escalated", "Resolved"];

const reasonBank = [
  ["Unusual transaction amount", "Transaction is 4.2x the customer's 90-day average ticket size."],
  ["Device associated with multiple accounts", "Device fingerprint seen on 6 distinct customer accounts in 14 days."],
  ["Abnormal transaction velocity", "7 attempts in 9 minutes against 2 payment instruments."],
  ["Location mismatch", "Transaction geo is 3,180 km from the last known trusted location."],
  ["Previous suspicious activity", "Customer has 2 prior transactions escalated in the last 60 days."],
  ["Merchant fraud concentration", "Merchant fraud rate is 3.8% versus a 0.6% category baseline."],
  ["Card testing pattern", "Sequence of low-value authorisations preceded this charge."],
  ["High-risk corridor", "Cross-border corridor flagged by sanctions and fraud watchlists."],
];

/** Deterministic pseudo-random so mock data is stable between SSR and client. */
function rng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}

function pad(n: number) {
  return String(n).padStart(2, "0");
}

function buildTransaction(index: number): Transaction {
  const r = rng(index * 7919 + 13);
  const merchant = merchants[Math.floor(r() * merchants.length)];
  const customer = customers[Math.floor(r() * customers.length)];
  const method = methods[Math.floor(r() * methods.length)];
  const loc = locations[Math.floor(r() * locations.length)];
  const device = devices[Math.floor(r() * devices.length)];

  const bucket = r();
  const riskScore =
    bucket > 0.93
      ? 81 + Math.floor(r() * 19)
      : bucket > 0.78
        ? 61 + Math.floor(r() * 20)
        : bucket > 0.5
          ? 31 + Math.floor(r() * 30)
          : 4 + Math.floor(r() * 27);

  const riskLevel = riskLevelFromScore(riskScore);
  const aiRecommendation: Decision =
    riskScore > 80 ? "HOLD" : riskScore > 60 ? "REVIEW" : "ALLOW";
  const decision: Decision =
    riskScore > 88 ? "HOLD" : riskScore > 58 ? "REVIEW" : "ALLOW";

  const amount =
    riskScore > 70
      ? 25000 + Math.floor(r() * 480000)
      : 480 + Math.floor(r() * 62000);

  const hour = 6 + Math.floor(r() * 17);
  const minute = Math.floor(r() * 60);
  const day = 1 + (index % 27);
  const timestamp = `2026-08-${pad(day)}T${pad(hour)}:${pad(minute)}:${pad(Math.floor(r() * 60))}`;

  const factorCount = riskScore > 60 ? 5 : riskScore > 30 ? 3 : 2;
  const picks = reasonBank.slice(0, factorCount);
  const weights = [32, 21, 17, 11, 9].slice(0, factorCount);
  const riskFactors = picks.map(([label, detail], i) => ({
    label,
    detail,
    contribution: Math.max(3, Math.round((weights[i] * riskScore) / 90)),
  }));

  return {
    id: `TXN-${90000 + index}`,
    timestamp,
    amount,
    currency: "INR",
    merchant: merchant.name,
    merchantId: merchant.id,
    customer: customer.name,
    customerId: customer.id,
    paymentMethod: method,
    country: loc.country,
    location: loc.city,
    device,
    ip: `${49 + Math.floor(r() * 160)}.${Math.floor(r() * 255)}.${Math.floor(r() * 255)}.${Math.floor(r() * 255)}`,
    riskScore,
    riskLevel,
    aiRecommendation,
    decision,
    investigationStatus:
      riskScore > 80
        ? statuses[1 + Math.floor(r() * 3)]
        : riskScore > 60
          ? statuses[Math.floor(r() * 3)]
          : "Resolved",
    explanation:
      riskScore > 60
        ? `This transaction was flagged because the amount is significantly higher than ${customer.name.split(" ").pop()}'s historical average, the originating device has appeared across multiple accounts, and the payment sits inside a high-risk behavioural pattern for ${merchant.name}.`
        : `No material anomalies were detected. Amount, device, geography and velocity all sit inside the customer's established behavioural envelope for ${merchant.category.toLowerCase()} spend.`,
    timeline: [
      { label: "Session login", time: `${pad(hour)}:${pad(Math.max(0, minute - 12))}`, detail: `Authenticated from ${loc.city} · MFA passed`, kind: "session" },
      { label: "Device detected", time: `${pad(hour)}:${pad(Math.max(0, minute - 10))}`, detail: `${device} · fingerprint match 71%`, kind: "device" },
      { label: "Transaction initiated", time: `${pad(hour)}:${pad(Math.max(0, minute - 2))}`, detail: `${method} · ₹${amount.toLocaleString("en-IN")} to ${merchant.name}`, kind: "transaction" },
      { label: "Risk engine triggered", time: `${pad(hour)}:${pad(minute)}`, detail: `Model v4.2 scored ${riskScore}/100 (${riskLevel})`, kind: "engine" },
      { label: "AI investigation", time: `${pad(hour)}:${pad(minute)}`, detail: `${factorCount} contributing factors correlated across 4 evidence sources`, kind: "ai" },
      { label: "Decision issued", time: `${pad(hour)}:${pad(minute + 1)}`, detail: `Recommendation ${aiRecommendation} · current state ${decision}`, kind: "decision" },
    ],
    related: Array.from({ length: 4 }).map((_, i) => {
      const rr = rng(index * 31 + i * 977);
      const m = merchants[Math.floor(rr() * merchants.length)];
      const s = 5 + Math.floor(rr() * 90);
      return {
        id: `TXN-${70000 + index * 4 + i}`,
        date: `2026-08-${pad(1 + Math.floor(rr() * 27))}`,
        amount: 900 + Math.floor(rr() * 90000),
        merchant: m.name,
        riskScore: s,
        decision: (s > 80 ? "HOLD" : s > 58 ? "REVIEW" : "ALLOW") as Decision,
      };
    }),
  };
}

export const mockTransactions: Transaction[] = Array.from({ length: 84 }).map((_, i) =>
  buildTransaction(i),
);

/** Featured hero transaction referenced across the product narrative. */
const featured = mockTransactions[0];
featured.id = "TXN-92831";
featured.amount = 42500;
featured.merchant = "Nova Electronics";
featured.merchantId = "MRC-1001";
featured.customer = "R. Venkatesh";
featured.customerId = "CUS-40218";
featured.paymentMethod = "Credit Card";
featured.location = "Mumbai, IN";
featured.country = "India";
featured.device = "Windows 11 · Chrome 126";
featured.ip = "103.214.88.17";
featured.timestamp = "2026-08-29T09:14:22";
featured.riskScore = 87;
featured.riskLevel = "CRITICAL";
featured.aiRecommendation = "REVIEW";
featured.decision = "REVIEW";
featured.investigationStatus = "Investigating";
featured.explanation =
  "This transaction was flagged because the transaction amount is significantly higher than the customer's historical average, the device has appeared across multiple accounts, and the transaction occurs within a high-risk behavioural pattern.";
featured.riskFactors = [
  { label: "Unusual transaction amount", contribution: 32, detail: "₹42,500 is 4.2x the customer's 90-day average ticket of ₹10,120." },
  { label: "Device associated with multiple accounts", contribution: 21, detail: "Device fingerprint linked to 6 distinct customer accounts in 14 days." },
  { label: "Abnormal transaction velocity", contribution: 17, detail: "Customer velocity up 280% versus a 30-day rolling baseline." },
  { label: "Location mismatch", contribution: 11, detail: "IP geolocation differs from the billing region and last trusted session." },
  { label: "Previous suspicious activity", contribution: 9, detail: "Two prior transactions on this card were escalated in the last 60 days." },
];

export const featuredTransactionId = featured.id;
