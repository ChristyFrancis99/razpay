export function formatINR(amount: number, compact = false): string {
  if (compact) {
    if (amount >= 1_00_00_000) return `₹${(amount / 1_00_00_000).toFixed(2)} Cr`;
    if (amount >= 1_00_000) return `₹${(amount / 1_00_000).toFixed(1)} L`;
    if (amount >= 1_000) return `₹${(amount / 1_000).toFixed(1)}K`;
  }
  return `₹${amount.toLocaleString("en-IN")}`;
}

export function formatNumber(value: number): string {
  return value.toLocaleString("en-IN");
}

export function formatTimestamp(iso: string): string {
  const [date, time] = iso.split("T");
  return time ? `${date} ${time.slice(0, 5)}` : date;
}

export function formatAge(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}

export function formatPercent(value: number, digits = 1): string {
  return `${value.toFixed(digits)}%`;
}
