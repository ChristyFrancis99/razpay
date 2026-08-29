import { createFileRoute } from "@tanstack/react-router";
import { DemoEntry } from "@/components/DemoEntry";

export const Route = createFileRoute("/")({
  component: DemoEntry,
});
