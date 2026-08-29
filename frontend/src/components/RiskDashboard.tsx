import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, ArrowUpRight, Bot, CheckCircle2, ChevronRight, CircleDot, Database, Gauge, Menu, Network, RefreshCw, Search, ShieldCheck, Store, XCircle } from "lucide-react";

const API = import.meta.env.VITE_API_BASE_URL || "/api";

type Tx = { id: string; risk: number; level: string; decision: string; probability: number; created?: string };
type Overview = { total_transactions: number; high_risk_transactions: number; critical_transactions: number; allow_count: number; review_count: number; hold_count: number; average_risk_score: number; note?: string };

type Copilot = { answer: string; risk_score?: number; decision?: string; key_findings: string[]; recommended_action: string; engine: string };

async function getJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || `API ${response.status}`);
  return response.json();
}

const riskClass = (level: string) => ({ LOW: "text-risk-low bg-risk-low-surface", MEDIUM: "text-risk-medium bg-risk-medium-surface", HIGH: "text-risk-high bg-risk-high-surface", CRITICAL: "text-risk-critical bg-risk-critical-surface" }[level] || "text-muted-foreground bg-muted");

export function RiskDashboard() {
  const [section, setSection] = useState("Overview");
  const [transactions, setTransactions] = useState<Tx[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [distribution, setDistribution] = useState<Record<string, number>>({});
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Tx | null>(null);
  const [copilotInput, setCopilotInput] = useState("");
  const [copilot, setCopilot] = useState<Copilot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [mobileNav, setMobileNav] = useState(false);

  const load = async () => {
    setLoading(true); setError("");
    try {
      const [tx, ov, dist] = await Promise.all([
        getJson<{ transactions: Array<{ transaction_id: string; risk_score: number; risk_level: string; recommended_decision: string; fraud_probability: number; created_at?: string }> }>("/transactions?limit=50"),
        getJson<Overview>("/analytics/overview"),
        getJson<{ risk_distribution: Record<string, number> }>("/analytics/risk-distribution"),
      ]);
      setTransactions(tx.transactions.map((t) => ({ id: t.transaction_id, risk: t.risk_score, level: t.risk_level, decision: t.recommended_decision, probability: t.fraud_probability, created: t.created_at })));
      setOverview(ov); setDistribution(dist.risk_distribution);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Backend unavailable");
    } finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, []);

  const filtered = useMemo(() => transactions.filter((t) => t.id.toLowerCase().includes(query.toLowerCase())), [transactions, query]);
  const totalRisk = Object.values(distribution).reduce((a, b) => a + b, 0) || 1;

  const askCopilot = async () => {
    if (!copilotInput.trim()) return;
    try {
      setCopilot(await getJson<Copilot>("/copilot", { method: "POST", body: JSON.stringify({ message: copilotInput, transaction_id: selected?.id }) }));
    } catch (e) { setError(e instanceof Error ? e.message : "Copilot unavailable"); }
  };

  const makeDecision = async (decision: string) => {
    if (!selected) return;
    try {
      await getJson("/risk/decision", { method: "POST", body: JSON.stringify({ transaction_id: selected.id, risk_score: selected.risk, override_decision: decision, actor: "investigator", reason: `Manual ${decision} decision from Risk Intelligence dashboard.` }) });
      await load();
      setSelected(null);
    } catch (e) { setError(e instanceof Error ? e.message : "Decision failed"); }
  };

  const nav = [
    ["Overview", Gauge], ["Transactions", Activity], ["Merchants", Store], ["Investigations", Network], ["Copilot", Bot], ["Audit trail", Database],
  ] as const;

  return <div className="min-h-screen bg-background text-foreground">
    <header className="sticky top-0 z-40 border-b border-border bg-navy/95 backdrop-blur">
      <div className="flex h-16 items-center justify-between px-4 lg:px-7">
        <div className="flex items-center gap-3"><button className="rounded-md p-2 hover:bg-accent lg:hidden" onClick={() => setMobileNav(!mobileNav)}>{mobileNav ? <XCircle size={20}/> : <Menu size={20}/>}</button><div className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground"><ShieldCheck size={20}/></div><div><div className="font-semibold tracking-tight">Razorpay Risk Intelligence</div><div className="hidden text-[11px] text-muted-foreground sm:block">Fraud & AML command center</div></div></div>
        <div className="flex items-center gap-2"><span className="hidden rounded-full border border-risk-low/30 bg-risk-low-surface px-3 py-1 text-xs text-risk-low sm:inline-flex"><CircleDot size={12} className="mr-1.5"/> Systems operational</span><button onClick={() => void load()} className="rounded-md border border-border p-2 hover:bg-accent" title="Refresh"><RefreshCw size={16}/></button><div className="grid size-9 place-items-center rounded-full border border-border bg-surface-raised text-xs font-semibold">CF</div></div>
      </div>
    </header>

    <div className="flex">
      <aside className={`${mobileNav ? "block" : "hidden"} fixed inset-y-16 left-0 z-30 w-64 border-r border-border bg-sidebar lg:sticky lg:top-16 lg:block lg:h-[calc(100vh-4rem)]`}>
        <div className="p-4"><div className="mb-3 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Workspace</div>{nav.map(([label, Icon]) => <button key={label} onClick={() => { setSection(label); setMobileNav(false); }} className={`mb-1 flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm transition ${section === label ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground"}`}><Icon size={17}/>{label}<ChevronRight size={14} className={`ml-auto transition ${section === label ? "opacity-100" : "opacity-0"}`}/></button>)}</div>
        <div className="absolute bottom-0 w-full border-t border-sidebar-border p-4"><div className="rounded-lg border border-sidebar-border bg-surface p-3"><div className="flex items-center gap-2 text-xs font-medium"><span className="size-2 rounded-full bg-risk-low"/> Investigator session</div><div className="mt-1 text-[11px] text-muted-foreground">AI-assisted decisions require human approval.</div></div></div>
      </aside>

      <main className="min-w-0 flex-1 p-4 lg:p-7">
        <div className="mx-auto max-w-[1500px]">
          <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">RISK OPERATIONS / {section.toUpperCase()}</div><h1 className="text-2xl font-semibold tracking-tight lg:text-3xl">{section === "Overview" ? "Risk Intelligence Overview" : section}</h1><p className="mt-1 max-w-2xl text-sm text-muted-foreground">Investigate transactions, understand model evidence, and record auditable risk decisions.</p></div><div className="numeric flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-xs text-muted-foreground"><span className="size-1.5 rounded-full bg-primary"/> LIVE DATA <span className="text-border">|</span> {new Date().toLocaleTimeString()}</div></div>

          {error && <div className="mb-5 flex items-center justify-between rounded-lg border border-risk-high/30 bg-risk-high-surface px-4 py-3 text-sm text-risk-high"><span><AlertTriangle size={15} className="mr-2 inline"/>{error}</span><button onClick={() => setError("")}><XCircle size={16}/></button></div>}

          {loading ? <div className="grid gap-4 md:grid-cols-4"><div className="panel h-28 animate-pulse"/><div className="panel h-28 animate-pulse"/><div className="panel h-28 animate-pulse"/><div className="panel h-28 animate-pulse"/></div> : <>
            {section === "Overview" && <>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {[["Scored transactions", overview?.total_transactions ?? 0, Activity], ["High risk", overview?.high_risk_transactions ?? 0, AlertTriangle], ["Critical", overview?.critical_transactions ?? 0, XCircle], ["Average risk", overview?.average_risk_score ?? 0, Gauge]].map(([label, value, Icon]) => <div className="panel p-5" key={String(label)}><div className="flex items-center justify-between"><span className="text-xs text-muted-foreground">{label}</span><Icon size={17} className="text-primary"/></div><div className="numeric mt-3 text-3xl font-semibold">{value}</div><div className="mt-2 text-[11px] text-muted-foreground">Current API-scored population</div></div>)}
              </div>
              <div className="mt-5 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
                <section className="panel p-5"><div className="mb-5 flex items-center justify-between"><div><h2 className="font-semibold">Risk distribution</h2><p className="text-xs text-muted-foreground">Scored transactions by risk level</p></div><ArrowUpRight size={17} className="text-muted-foreground"/></div>{["LOW","MEDIUM","HIGH","CRITICAL"].map((level) => <div key={level} className="mb-4 last:mb-0"><div className="mb-1.5 flex justify-between text-xs"><span>{level}</span><span className="numeric text-muted-foreground">{distribution[level] || 0}</span></div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className={`h-full rounded-full ${level === "LOW" ? "bg-risk-low" : level === "MEDIUM" ? "bg-risk-medium" : level === "HIGH" ? "bg-risk-high" : "bg-risk-critical"}`} style={{ width: `${Math.max(2, ((distribution[level] || 0) / totalRisk) * 100)}%` }}/></div></div>)}</section>
                <section className="panel grid-backdrop p-5"><div className="flex items-center gap-3"><div className="grid size-10 place-items-center rounded-lg bg-ai-surface text-ai"><Bot size={20}/></div><div><h2 className="font-semibold">AI Risk Copilot</h2><p className="text-xs text-muted-foreground">Ask about a transaction or merchant</p></div></div><div className="mt-5 flex gap-2"><input value={copilotInput} onChange={(e) => setCopilotInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && void askCopilot()} placeholder="Why was this transaction flagged?" className="min-w-0 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none ring-primary/40 focus:ring-2"/><button onClick={() => void askCopilot()} className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground">Ask</button></div>{copilot && <div className="mt-4 rounded-lg border border-border bg-surface p-4"><p className="text-sm leading-6">{copilot.answer}</p><div className="mt-3 grid gap-2">{copilot.key_findings.slice(0,3).map((f) => <div key={f} className="text-xs text-muted-foreground"><span className="mr-2 text-primary">•</span>{f}</div>)}</div><div className="mt-3 text-[10px] uppercase tracking-wider text-ai">{copilot.engine} / recommended {copilot.recommended_action}</div></div>}</section>
              </div>
            </>}

            {(section === "Transactions" || section === "Investigations") && <section className="panel overflow-hidden"><div className="flex flex-col gap-3 border-b border-border p-4 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="font-semibold">Transaction investigation queue</h2><p className="text-xs text-muted-foreground">Select a transaction to inspect its risk decision.</p></div><div className="relative"><Search size={15} className="absolute left-3 top-2.5 text-muted-foreground"/><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search transaction ID" className="w-full rounded-md border border-input bg-background py-2 pl-9 pr-3 text-sm sm:w-64"/></div></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-surface-raised text-[10px] uppercase tracking-wider text-muted-foreground"><tr><th className="px-4 py-3">Transaction</th><th className="px-4 py-3">Fraud probability</th><th className="px-4 py-3">Risk</th><th className="px-4 py-3">Recommendation</th><th className="px-4 py-3"/></tr></thead><tbody>{filtered.map((t) => <tr key={t.id} onClick={() => setSelected(t)} className="cursor-pointer border-t border-border hover:bg-accent/40"><td className="numeric px-4 py-3 font-medium">{t.id}</td><td className="numeric px-4 py-3">{(t.probability * 100).toFixed(1)}%</td><td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${riskClass(t.level)}`}>{t.level} · {t.risk}</span></td><td className="px-4 py-3 text-xs">{t.decision}</td><td className="px-4 py-3 text-right"><ChevronRight size={15} className="text-muted-foreground"/></td></tr>)}{filtered.length === 0 && <tr><td colSpan={5} className="px-4 py-12 text-center text-sm text-muted-foreground">No scored transactions found.</td></tr>}</tbody></table></div></section>}

            {section === "Merchants" && <section className="panel p-6"><div className="flex items-start gap-4"><div className="grid size-11 place-items-center rounded-lg bg-primary/10 text-primary"><Store size={21}/></div><div><h2 className="font-semibold">Merchant risk investigation</h2><p className="mt-1 text-sm text-muted-foreground">Merchant endpoints are connected to the backend and can be explored by merchant/entity ID.</p></div></div><div className="mt-6 rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">Use the API-backed merchant investigation route <span className="numeric text-foreground">GET /api/merchants/:merchant_id</span> from your integration or extend this view with merchant search when entity data is loaded.</div></section>}

            {section === "Copilot" && <section className="panel mx-auto max-w-4xl p-6"><div className="mb-6 flex items-center gap-3"><div className="grid size-11 place-items-center rounded-lg bg-ai-surface text-ai"><Bot/></div><div><h2 className="font-semibold">Risk Intelligence Copilot</h2><p className="text-xs text-muted-foreground">Evidence-first assistance for investigators</p></div></div><div className="flex gap-2"><input autoFocus value={copilotInput} onChange={(e) => setCopilotInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && void askCopilot()} placeholder="Ask: explain the strongest risk factors" className="min-w-0 flex-1 rounded-md border border-input bg-background px-3 py-3 text-sm"/><button onClick={() => void askCopilot()} className="rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground">Analyze</button></div>{copilot && <div className="mt-5 space-y-4"><div className="rounded-lg border border-border bg-surface p-5"><p className="leading-7">{copilot.answer}</p></div><div className="grid gap-3 sm:grid-cols-2">{copilot.key_findings.map((f) => <div key={f} className="rounded-md border border-border p-3 text-sm"><CheckCircle2 size={15} className="mr-2 inline text-primary"/>{f}</div>)}</div></div>}</section>}

            {section === "Audit trail" && <section className="panel p-6"><h2 className="font-semibold">Auditable decisioning</h2><p className="mt-1 text-sm text-muted-foreground">Every manual override is persisted through the risk decision endpoint and written to the audit log.</p><div className="mt-5 grid gap-3 md:grid-cols-3"><div className="rounded-lg border border-border p-4"><CheckCircle2 className="text-risk-low" size={18}/><div className="mt-3 text-sm font-medium">Human-in-the-loop</div><div className="mt-1 text-xs text-muted-foreground">Investigator remains the final decision maker.</div></div><div className="rounded-lg border border-border p-4"><Database className="text-primary" size={18}/><div className="mt-3 text-sm font-medium">Immutable context</div><div className="mt-1 text-xs text-muted-foreground">Actor, reason, score and decision are recorded.</div></div><div className="rounded-lg border border-border p-4"><Network className="text-ai" size={18}/><div className="mt-3 text-sm font-medium">Explainability</div><div className="mt-1 text-xs text-muted-foreground">Model evidence is available before an override.</div></div></div></section>}
          </>}
        </div>
      </main>

      {selected && <div className="fixed inset-0 z-50 bg-black/60 p-4 backdrop-blur-sm" onClick={() => setSelected(null)}><div className="ml-auto h-full w-full max-w-xl overflow-y-auto border-l border-border bg-background p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}><div className="flex items-start justify-between"><div><div className="text-[10px] uppercase tracking-widest text-primary">Transaction investigation</div><h2 className="numeric mt-1 text-xl font-semibold">{selected.id}</h2></div><button onClick={() => setSelected(null)} className="rounded-md p-2 hover:bg-accent"><XCircle size={18}/></button></div><div className={`mt-6 rounded-xl p-5 ${riskClass(selected.level)}`}><div className="text-xs uppercase tracking-wider">Current risk</div><div className="numeric mt-1 text-4xl font-semibold">{selected.risk}<span className="text-sm font-normal opacity-70"> / 100</span></div><div className="mt-2 text-sm">{selected.level} · {(selected.probability * 100).toFixed(1)}% fraud probability</div></div><div className="mt-5 rounded-lg border border-border p-4"><div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Recommended action</div><div className="mt-2 text-lg font-semibold">{selected.decision}</div><p className="mt-2 text-sm leading-6 text-muted-foreground">Review the model explanation and supporting evidence before overriding the recommendation.</p></div><div className="mt-5"><div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Decision</div><div className="grid grid-cols-3 gap-2"><button onClick={() => void makeDecision("ALLOW")} className="rounded-md border border-risk-low/30 bg-risk-low-surface px-3 py-2 text-xs font-medium text-risk-low">Allow</button><button onClick={() => void makeDecision("REVIEW")} className="rounded-md border border-risk-medium/30 bg-risk-medium-surface px-3 py-2 text-xs font-medium text-risk-medium">Review</button><button onClick={() => void makeDecision("HOLD")} className="rounded-md border border-risk-critical/30 bg-risk-critical-surface px-3 py-2 text-xs font-medium text-risk-critical">Hold</button></div></div><div className="mt-6 rounded-lg border border-ai/20 bg-ai-surface/50 p-4"><div className="flex items-center gap-2 text-sm font-medium text-ai"><Bot size={16}/> Ask Copilot about this transaction</div><div className="mt-3 flex gap-2"><input value={copilotInput} onChange={(e) => setCopilotInput(e.target.value)} placeholder="Explain this risk" className="min-w-0 flex-1 rounded-md border border-input bg-background px-3 py-2 text-xs"/><button onClick={() => void askCopilot()} className="rounded-md bg-ai px-3 py-2 text-xs font-medium text-ai-foreground">Ask</button></div>{copilot && <p className="mt-3 text-xs leading-5 text-muted-foreground">{copilot.answer}</p>}</div></div></div>}
    </div>
  </div>;
}
