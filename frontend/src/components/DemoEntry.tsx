import { useEffect, useState } from "react";
import { PlatformShell } from "@/components/PlatformShell";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

export function DemoEntry() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const start = async () => {
      try {
        const existing = localStorage.getItem("risk-token");
        if (existing) {
          const check = await fetch(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${existing}` },
          });
          if (check.ok) {
            if (!cancelled) setReady(true);
            return;
          }
          localStorage.removeItem("risk-token");
          localStorage.removeItem("risk-user");
        }

        const response = await fetch(`${API}/auth/demo`, { method: "POST" });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data?.detail || `Unable to start demo session (${response.status})`);
        }

        localStorage.setItem("risk-token", data.access_token);
        localStorage.setItem("risk-user", JSON.stringify(data.user));
        if (!cancelled) setReady(true);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Unable to start the platform");
      }
    };

    void start();
    return () => { cancelled = true; };
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-background text-foreground grid place-items-center p-6">
        <div className="panel max-w-lg p-6 text-center">
          <h1 className="text-xl font-semibold">Risk platform unavailable</h1>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
          <p className="mt-4 text-xs text-muted-foreground">Make sure the FastAPI backend is running on port 8000, then refresh.</p>
        </div>
      </div>
    );
  }

  if (!ready) {
    return <div className="min-h-screen bg-background grid place-items-center text-sm text-muted-foreground">Starting Risk Intelligence…</div>;
  }

  return <PlatformShell />;
}
