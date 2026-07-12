import { createFileRoute } from "@tanstack/react-router";
import MaintenancePage from "@/pages/MaintenancePage";

export const Route = createFileRoute("/maintenance")({
  head: () => ({
    meta: [
      { title: "Maintenance — TransitOps" },
      { name: "description", content: "Vehicle repair logs and shop workflow." },
    ],
  }),
  component: MaintenancePage,
});
