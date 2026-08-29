import { lazy, Suspense } from "react";
import { createFileRoute } from "@tanstack/react-router";

// PlatformShell is a named export, so adapt it to React.lazy's required
// { default: Component } module shape. The previous loader returned the
// module directly, which caused TanStack Start's SSR renderer to fail with
// the generic "The application could not render this view" page.
const PlatformShell = lazy(() =>
  import("@/components/PlatformShell").then((module) => ({
    default: module.PlatformShell,
  })),
);

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
