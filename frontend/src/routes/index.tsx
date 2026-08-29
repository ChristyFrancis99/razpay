import { createFileRoute } from "@tanstack/react-router";
import { PlatformShell } from "@/components/PlatformShell";

export const Route = createFileRoute("/")({
  component: PlatformShell,
});
