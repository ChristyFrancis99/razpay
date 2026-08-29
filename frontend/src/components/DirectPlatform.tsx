import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Bot, CheckCircle2, Database, Gauge, Menu, Network, RefreshCw, Search, ShieldCheck, Store, Users, X, XCircle } from "lucide-react";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
type Tx = { transaction_id: string; fraud_probability: number; risk_score: number; risk_level: string; recommended_decision: string; final_decision?: string; created_at?: string; explanation?: string; risk_factors?: { feature: string; impact: number; direction: string; description: string }[] };
type Merchant = { merchant_id: string; transaction_volume: number; fraud_count: number; fraud_rate: number; average_transaction_amount: number; merchant_risk_score: number; merchant_risk_level: string };
type Audit = { id: number; timestamp: string; transaction_id: string; previous_decision?: string; new_decision: string; risk_score: number; actor: string; reason: string };
type Overview = { total_transactions: number; fraud_transactions: number; fraud_rate: number; high_risk_transactions: number; critical_transactions: number; allow_count: number; review_count: number; hold_count: number; average_risk_score: number; data_source: string };
type Health = { status: string; model_loaded: boolean; model_name?: string; data_source?: string };

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("risk-token");
  const headers = { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options?.headers || {}) };
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || `API ${response.status}`);
  return body as T;
}

const riskClass = (level: string) => level === "LOW" ? "text-risk-low bg-risk-low-surface" : level === "MEDIUM" ? "text-risk-medium bg-risk-medium-surface" : level === "HIGH" ? "text-risk-high bg-risk-high-surface" : "text-risk-critical bg-risk-critical-surface";

export function DirectPlatform() {
  const [ready, setReady] = useState(false);
  const [startupError, setStartupError] = useState("");
  const [section, setSection] = useState("Overview");
  const [txs, setTxs] = useState<Tx[]>([]);
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [distribution, setDistribution] = useState<Record<string, number>>({});
  const [selected, setSelected] = useState<Tx | null>(null);
  const [merchantId, setMerchantId] = useState("");
  const [merchantDetail, setMerchantDetail] = useState<Record<string, unknown> | null>(null);
  const [query, setQuery] = useState("");
  const [copilotInput, setCopilotInput] = useState("");
  const [copilot, setCopilot] = useState<{ answer: string; key_findings: string[]; recommended_action: string; engine: string } | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [mobile, setMobile] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState("INVESTIGATOR");
  const [userMessage, setUserMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    const start = async () => {
      try {
        const existing = localStorage.getItem("risk-token");
        if (!existing) {
          const response = await fetch(`${API}/auth/demo`, { method: "POST" });
          const data = await response.json().catch(() => ({}));
          if (!response.ok) throw new Error(data?.detail || `Demo session failed (${response.status})`);
          localStorage.setItem("risk-token", data.access_token);
          localStorage.setItem("risk-user", JSON.stringify(data.user));
        } else {
          const check = await fetch(`${API}/auth/me`, { headers: { Authorization: `Bearer ${existing}` } });
          if (!check.ok) {
            localStorage.removeItem("risk-token");
            localStorage.removeItem("risk-user");
            const response = await fetch(`${API}/auth/demo`, { method: "POST" });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(data?.detail || `Demo session failed (${response.status})`);
            localStorage.setItem("risk-token", data.access_token);
            localStorage.setItem("risk-user", JSON.stringify(data.user));
          }
        }
        if (!cancelled) setReady(true);
      } catch (e) {
        if (!cancelled) setStartupError(e instanceof Error ? e.message : "Unable to start the platform");
      }
    };
    void start();
    return () => { cancelled = true; };
  }, []);

  const load = async () => {
    setLoading(true); setError("");
    try {
      const [o, d, t, h, m, a] = await Promise.all([
        api<Overview>("/analytics/overview"),
        api<{ risk_distribution: Record<string, number> }>("/analytics/risk-distribution"),
        api<{ transactions: Tx[] }>("/transactions?limit=100"),
        api<Health>("/health"),
        api<{ merchants: Merchant[] }>("/merchants?limit=50"),
        api<Audit[]>("/audit-logs?limit=100"),
      ]);
      setOverview(o); setDistribution(d.risk_distribution); setTxs(t.transactions); setHealth(h); setMerchants(m.merchants); setAudit(a);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to load platform data"); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (ready) void load(); }, [ready]);

  const filtered = useMemo(() => txs.filter(t => t.transaction_id.toLowerCase().includes(query.toLowerCase())), [txs, query]);
  const decide = async (decision: string) => {
    if (!selected) return;
    try { await api("/risk/decision", { method: "POST", body: JSON.stringify({ transaction_id: selected.transaction_id, risk_score: selected.risk_score, override_decision: decision, reason: `Demo administrator recorded ${decision} after investigation.` }) }); await load(); setSelected(null); }
    catch (e) { setError(e instanceof Error ? e.message : "Decision failed"); }
  };
  const inspectMerchant = async () => {
    if (!merchantId.trim()) return;
    try { setMerchantDetail(await api(`/merchants/${encodeURIComponent(merchantId.trim())}`)); }
    catch (e) { setError(e instanceof Error ? e.message : "Merchant not found"); }
  };
  const ask = async () => {
    if (!copilotInput.trim()) return;
    try { setCopilot(await api("/copilot", { method: "POST", body: JSON.stringify({ message: copilotInput, transaction_id: selected?.transaction_id, merchant_id: merchantId || undefined }) })); }
    catch (e) { setError(e instanceof Error ? e.message : "Copilot unavailable"); }
  };
  const createUser = async () => {
    setUserMessage("");
    try { await api("/auth/users", { method: "POST", body: JSON.stringify({ username: newUsername, password: newPassword, role: newRole }) }); setNewUsername(""); setNewPassword(""); setUserMessage("User created successfully."); }
    catch (e) { setUserMessage(e instanceof Error ? e.message : "Unable to create user"); }
  };

  if (startupError) return <div className="min-h-screen bg-background grid place-items-center p-6 text-foreground"><div className="panel max-w-lg p-7 text-center"><ShieldCheck className="mx-auto text-primary" size={34}/><h1 className="mt-4 text-xl font-semibold">Risk platform unavailable</h1><p className="mt-2 text-sm text-muted-foreground">{startupError}</p><p className="mt-4 text-xs text-muted-foreground">Start FastAPI on port 8000 and refresh.</p></div></div>;
  if (!ready) return <div className="min-h-screen bg-background grid place-items-center text-sm text-muted-foreground">Starting Risk Intelligence…</div>;

  const nav: [string, typeof Gauge][] = [["Overview", Gauge], ["Transactions", Activity], ["Investigations", Network], ["Merchants", Store], ["Copilot", Bot], ["Audit trail", Database], ["System health", CheckCircle2], ["Users & roles", Users]];
  return <div className="min-h-screen bg-background text-foreground">
    <header className="sticky top-0 z-50 border-b border-border bg-navy/95 backdrop-blur"><div className="flex h-16 items-center justify-between px-4 lg:px-7"><div className="flex items-center gap-3"><button className="rounded-md p-2 hover:bg-accent lg:hidden" onClick={() => setMobile(!mobile)}>{mobile ? <X size={20}/> : <Menu size={20}/>}</button><div className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground"><ShieldCheck size={20}/></div><div><b>Razorpay Risk Intelligence</b><div className="hidden text-[11px] text-muted-foreground sm:block">Fraud, AML & transaction risk operations</div></div></div><button onClick={() => void load()} className="rounded-md border border-border p-2 hover:bg-accent" title="Refresh"><RefreshCw size={16}/></button></div></header>
    <div className="flex"><aside className={`${mobile ? "block" : "hidden"} fixed inset-y-16 left-0 z-40 w-64 border-r border-border bg-sidebar lg:sticky lg:top-16 lg:block lg:h-[calc(100vh-4rem)]`}><div className="p-4"><div className="mb-3 px-2 text-[10px] font-semibold uppercase tracking-[.18em] text-muted-foreground">ADMINISTRATOR · DEMO</div>{nav.map(([label, Icon]) => <button key={label} onClick={() => { setSection(label); setMobile(false); }} className={`mb-1 flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm ${section === label ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground"}`}><Icon size={17}/>{label}</button>)}</div></aside>
      <main className="min-w-0 flex-1 p-4 lg:p-7"><div className="mx-auto max-w-[1500px]"><div className="mb-6 flex flex-col justify-between gap-3 md:flex-row md:items-end"><div><div className="mb-2 text-[10px] font-semibold uppercase tracking-[.2em] text-primary">RISK OPERATIONS / {section.toUpperCase()}</div><h1 className="text-2xl font-semibold lg:text-3xl">{section}</h1><p className="mt-1 text-sm text-muted-foreground">Explainable risk decisions with human oversight and an auditable trail.</p></div><div className="numeric rounded-md border border-border bg-surface px-3 py-2 text-xs text-muted-foreground">{health?.model_name || "Model"} · {health?.model_loaded ? "READY" : "NOT READY"}</div></div>
      {error && <div className="mb-5 flex items-center justify-between rounded-lg border border-risk-high/30 bg-risk-high-surface px-4 py-3 text-sm text-risk-high"><span><AlertTriangle size={15} className="mr-2 inline"/>{error}</span><button onClick={() => setError("")}><XCircle size={16}/></button></div>}
      {loading ? <div className="grid gap-4 md:grid-cols-4">{[1,2,3,4].map(i => <div key={i} className="panel h-28 animate-pulse"/>)}</div> : <>
        {section === "Overview" && <><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[["Transactions", overview?.total_transactions ?? 0],["Fraud", overview?.fraud_transactions ?? 0],["High risk", overview?.high_risk_transactions ?? 0],["Critical", overview?.critical_transactions ?? 0]].map(([l,v]) => <div className="panel p-5" key={String(l)}><span className="text-xs text-muted-foreground">{l}</span><div className="numeric mt-3 text-3xl font-semibold">{v}</div></div>)}</div><div className="mt-5 grid gap-5 lg:grid-cols-2"><section className="panel p-5"><h2 className="font-semibold">Decision posture</h2><div className="mt-5 grid grid-cols-3 gap-3">{[["ALLOW",overview?.allow_count],["REVIEW",overview?.review_count],["HOLD",overview?.hold_count]].map(([l,v]) => <div key={String(l)} className="rounded-lg border border-border p-4"><div className="text-xs text-muted-foreground">{l}</div><div className="numeric mt-2 text-2xl font-semibold">{v ?? 0}</div></div>)}</div></section><section className="panel p-5"><h2 className="font-semibold">Risk distribution</h2>{["LOW","MEDIUM","HIGH","CRITICAL"].map(l => { const total=Object.values(distribution).reduce((a,b)=>a+b,0)||1; const n=distribution[l]||0; return <div key={l} className="mt-4"><div className="mb-1 flex justify-between text-xs"><span>{l}</span><span>{n}</span></div><div className="h-2 rounded-full bg-muted"><div className={`h-full rounded-full ${l === "LOW" ? "bg-risk-low" : l === "MEDIUM" ? "bg-risk-medium" : l === "HIGH" ? "bg-risk-high" : "bg-risk-critical"}`} style={{width:`${Math.max(n?2:0,n/total*100)}%`}}/></div></div>})}</section></div></>}
        {(section === "Transactions" || section === "Investigations") && <section className="panel overflow-hidden"><div className="flex flex-col gap-3 border-b border-border p-4 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="font-semibold">Transaction investigation queue</h2><p className="text-xs text-muted-foreground">Select a transaction for evidence, explanation and decision.</p></div><div className="relative"><Search size={15} className="absolute left-3 top-2.5 text-muted-foreground"/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search transaction ID" className="w-full rounded-md border border-input bg-background py-2 pl-9 pr-3 text-sm sm:w-64"/></div></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-surface-raised text-[10px] uppercase text-muted-foreground"><tr><th className="px-4 py-3">Transaction</th><th className="px-4 py-3">Probability</th><th className="px-4 py-3">Risk</th><th className="px-4 py-3">Decision</th></tr></thead><tbody>{filtered.map(t=><tr key={t.transaction_id} onClick={()=>setSelected(t)} className="cursor-pointer border-t border-border hover:bg-accent/40"><td className="numeric px-4 py-3 font-medium">{t.transaction_id}</td><td className="numeric px-4 py-3">{(t.fraud_probability*100).toFixed(1)}%</td><td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${riskClass(t.risk_level)}`}>{t.risk_level} · {t.risk_score}</span></td><td className="px-4 py-3 text-xs">{t.final_decision || t.recommended_decision}</td></tr>)}</tbody></table></div></section>}
        {section === "Merchants" && <section className="grid gap-5 lg:grid-cols-[1.1fr_.9fr]"><div className="panel overflow-hidden"><div className="flex items-center justify-between border-b border-border p-4"><div><h2 className="font-semibold">Merchant intelligence</h2><p className="text-xs text-muted-foreground">Backend-derived entity risk grouping</p></div><div className="flex gap-2"><input value={merchantId} onChange={e=>setMerchantId(e.target.value)} placeholder="Merchant ID" className="w-36 rounded-md border border-input bg-background px-3 py-2 text-sm"/><button onClick={()=>void inspectMerchant()} className="rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground">Investigate</button></div></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-surface-raised text-[10px] uppercase text-muted-foreground"><tr><th className="px-4 py-3">Entity</th><th className="px-4 py-3">Volume</th><th className="px-4 py-3">Fraud rate</th><th className="px-4 py-3">Risk</th></tr></thead><tbody>{merchants.map(m=><tr key={m.merchant_id} onClick={()=>{setMerchantId(m.merchant_id);void inspectMerchant();}} className="cursor-pointer border-t border-border hover:bg-accent/40"><td className="numeric px-4 py-3 font-medium">{m.merchant_id}</td><td className="numeric px-4 py-3">{m.transaction_volume}</td><td className="numeric px-4 py-3">{(m.fraud_rate*100).toFixed(2)}%</td><td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${riskClass(m.merchant_risk_level)}`}>{m.merchant_risk_level} · {m.merchant_risk_score}</span></td></tr>)}</tbody></table></div></div><div className="panel p-5"><h2 className="font-semibold">Investigation</h2>{merchantDetail ? <pre className="mt-4 max-h-[500px] overflow-auto whitespace-pre-wrap rounded-lg bg-surface-raised p-4 text-xs text-muted-foreground">{JSON.stringify(merchantDetail,null,2)}</pre> : <p className="mt-4 text-sm text-muted-foreground">Select a merchant to inspect its profile and risk signals.</p>}</div></section>}
        {section === "Copilot" && <section className="panel mx-auto max-w-4xl p-6"><div className="flex items-center gap-3"><div className="grid size-11 place-items-center rounded-lg bg-ai-surface text-ai"><Bot/></div><div><h2 className="font-semibold">Risk Intelligence Copilot</h2><p className="text-xs text-muted-foreground">Evidence-first investigation assistant</p></div></div><div className="mt-5 flex gap-2"><input value={copilotInput} onChange={e=>setCopilotInput(e.target.value)} onKeyDown={e=>e.key === "Enter" && void ask()} placeholder="Why was this transaction flagged?" className="min-w-0 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"/><button onClick={()=>void ask()} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Ask</button></div>{copilot && <div className="mt-5 rounded-lg border border-border bg-surface p-5"><p className="text-sm leading-6">{copilot.answer}</p><div className="mt-4 grid gap-2">{copilot.key_findings.map(f=><div key={f} className="text-xs text-muted-foreground">• {f}</div>)}</div><div className="mt-4 text-[10px] uppercase tracking-wider text-ai">{copilot.engine} · recommended {copilot.recommended_action}</div></div>}</section>}
        {section === "Audit trail" && <section className="panel overflow-hidden"><div className="border-b border-border p-4"><h2 className="font-semibold">Auditable decisions</h2></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-surface-raised text-[10px] uppercase text-muted-foreground"><tr><th className="px-4 py-3">Time</th><th className="px-4 py-3">Transaction</th><th className="px-4 py-3">Change</th><th className="px-4 py-3">Actor</th><th className="px-4 py-3">Reason</th></tr></thead><tbody>{audit.map(a=><tr key={a.id} className="border-t border-border"><td className="px-4 py-3 text-xs text-muted-foreground">{new Date(a.timestamp).toLocaleString()}</td><td className="numeric px-4 py-3">{a.transaction_id}</td><td className="px-4 py-3">{a.previous_decision || "—"} → <b>{a.new_decision}</b></td><td className="px-4 py-3 text-xs">{a.actor}</td><td className="max-w-md px-4 py-3 text-xs text-muted-foreground">{a.reason}</td></tr>)}</tbody></table></div></section>}
        {section === "System health" && <section className="grid gap-4 md:grid-cols-3"><div className="panel p-5"><span className="text-xs text-muted-foreground">API</span><div className="mt-3 flex items-center gap-2 font-semibold"><CheckCircle2 className="text-risk-low"/> Operational</div></div><div className="panel p-5"><span className="text-xs text-muted-foreground">Model</span><div className="mt-3 flex items-center gap-2 font-semibold">{health?.model_loaded ? <><CheckCircle2 className="text-risk-low"/> Loaded</> : <><XCircle className="text-risk-high"/> Unavailable</>}</div><p className="mt-2 text-xs text-muted-foreground">{health?.model_name || "—"}</p></div><div className="panel p-5"><span className="text-xs text-muted-foreground">Data source</span><div className="mt-3 font-semibold">{health?.data_source || "Unknown"}</div></div></section>}
        {section === "Users & roles" && <section className="panel max-w-2xl p-6"><h2 className="font-semibold">Create platform user</h2><p className="mt-1 text-xs text-muted-foreground">Demo mode is administrator-backed; new users use the real backend authorization layer.</p><div className="mt-5 grid gap-3 sm:grid-cols-2"><input value={newUsername} onChange={e=>setNewUsername(e.target.value)} placeholder="Username" className="rounded-md border border-input bg-background px-3 py-2 text-sm"/><input value={newPassword} onChange={e=>setNewPassword(e.target.value)} placeholder="Password" type="password" className="rounded-md border border-input bg-background px-3 py-2 text-sm"/><select value={newRole} onChange={e=>setNewRole(e.target.value)} className="rounded-md border border-input bg-background px-3 py-2 text-sm"><option>INVESTIGATOR</option><option>MANAGER</option><option>ADMINISTRATOR</option></select><button onClick={()=>void createUser()} className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground">Create user</button></div>{userMessage && <p className="mt-4 text-xs text-muted-foreground">{userMessage}</p>}</section>}
      </>}</div></main></div>

    {selected && <div className="fixed inset-0 z-[60] grid place-items-center bg-black/60 p-4"><div className="max-h-[90vh] w-full max-w-3xl overflow-auto rounded-xl border border-border bg-background p-6"><div className="flex items-start justify-between"><div><div className="text-[10px] uppercase tracking-wider text-primary">Transaction investigation</div><h2 className="mt-1 text-xl font-semibold">{selected.transaction_id}</h2></div><button onClick={()=>setSelected(null)} className="rounded-md p-2 hover:bg-accent"><X/></button></div><div className="mt-5 grid gap-4 sm:grid-cols-4"><div className="panel p-4"><span className="text-xs text-muted-foreground">Fraud probability</span><b className="numeric mt-2 block text-xl">{(selected.fraud_probability*100).toFixed(1)}%</b></div><div className="panel p-4"><span className="text-xs text-muted-foreground">Risk score</span><b className="numeric mt-2 block text-xl">{selected.risk_score}</b></div><div className="panel p-4"><span className="text-xs text-muted-foreground">Risk level</span><b className={`mt-2 inline-block rounded-full px-2 py-1 text-xs ${riskClass(selected.risk_level)}`}>{selected.risk_level}</b></div><div className="panel p-4"><span className="text-xs text-muted-foreground">Recommendation</span><b className="mt-2 block text-sm">{selected.recommended_decision}</b></div></div>{selected.explanation && <div className="mt-5 rounded-lg border border-border bg-surface p-4"><h3 className="font-semibold">Explanation</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">{selected.explanation}</p></div>}{selected.risk_factors?.length ? <div className="mt-5"><h3 className="font-semibold">Risk factors</h3><div className="mt-3 grid gap-2">{selected.risk_factors.map(f=><div key={f.feature} className="rounded-lg border border-border p-3 text-sm"><b>{f.feature}</b><span className="ml-2 text-xs text-muted-foreground">{f.direction} · impact {f.impact}</span><p className="mt-1 text-xs text-muted-foreground">{f.description}</p></div>)}</div></div> : null}<div className="mt-6 flex flex-wrap gap-2"><button onClick={()=>void decide("ALLOW")} className="rounded-md border border-risk-low/40 px-4 py-2 text-sm font-medium text-risk-low">Allow</button><button onClick={()=>void decide("REVIEW")} className="rounded-md border border-risk-medium/40 px-4 py-2 text-sm font-medium text-risk-medium">Review</button><button onClick={()=>void decide("HOLD")} className="rounded-md border border-risk-critical/40 px-4 py-2 text-sm font-medium text-risk-critical">Hold</button></div></div></div>}
  </div>;
}
