import { useEffect, useState } from "react";
import { PlatformShell } from "@/components/PlatformShell";

const API = import.meta.env.VITE_API_BASE_URL || "/api";

export function DemoEntry() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const existing = localStorage.getItem("risk-token");
    if (existing) {
      setReady(true);
      return;
    }

    fetch(`${API}/auth/demo`, { method: "POST" })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data?.detail || `Demo access failed (${response.status})`);
        localStorage.setItem("risk-token", data.access_token);
        localStorage.setItem("risk-user", JSON.stringify(data.user));
        setReady(true);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to start demo session"));
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-background text-foreground grid place-items-center p-6">
        <div className="panel max-w-lg p-6 text-center">
          <h1 className="text-xl font-semibold">Risk platform unavailable</h1>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
          <p className="mt-4 text-xs text-muted-foreground">Start the FastAPI backend in development mode and refresh this page.</p>
        </div>
      </div>
    );
  }

  if (!ready) {
    return <div className="min-h-screen bg-background grid place-items-center text-sm text-muted-foreground">Starting Risk Intelligence…</div>;
  }

  return <PlatformShell />;
}
