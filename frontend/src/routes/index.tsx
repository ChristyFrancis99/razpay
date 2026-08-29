import { lazy, Suspense } from "react";
import { createFileRoute } from "@tanstack/react-router";

const PlatformShell = lazy(async () => {
  if (typeof window !== "undefined") {
    const originalFetch = window.fetch.bind(window);
    const localApi = "http://127.0.0.1:8000/api";

    window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
      let request = input;
      const rawUrl = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;

      // Keep local development traffic on the FastAPI server even if an old
      // VITE_API_BASE_URL or browser cache points at the Vite port.
      if (rawUrl.startsWith("/api/")) {
        request = new URL(rawUrl, window.location.origin).toString().startsWith(window.location.origin)
          ? `${localApi}${rawUrl.slice(4)}`
          : input;
      } else if (rawUrl.startsWith("http://localhost:8000/api/") || rawUrl.startsWith("http://127.0.0.1:8000/api/")) {
        request = rawUrl.replace("http://localhost:8000", "http://127.0.0.1:8000");
      }

      return originalFetch(request, init).catch((error: unknown) => {
        if (error instanceof TypeError && /fetch/i.test(error.message)) {
          throw new Error("Cannot reach the Risk API at http://127.0.0.1:8000. Make sure the FastAPI backend is running on port 8000.");
        }
        throw error;
      });
    };
  }

  return import("@/components/PlatformShell");
});

function App() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background grid place-items-center text-sm text-muted-foreground">Loading Risk Intelligence…</div>}>
      <PlatformShell />
    </Suspense>
  );
}

export const Route = createFileRoute("/")({
  component: App,
});
