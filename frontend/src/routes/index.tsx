import { createFileRoute } from "@tanstack/react-router";
import { DirectPlatform } from "@/components/DirectPlatform";

export const Route = createFileRoute("/")({
  component: DirectPlatform,
});
