import { createFileRoute } from "@tanstack/react-router";
import { RiskDashboard } from "@/components/RiskDashboard";

export const Route = createFileRoute("/")({
  component: RiskDashboard,
});
