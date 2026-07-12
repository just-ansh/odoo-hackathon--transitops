import { createFileRoute } from "@tanstack/react-router";
import DashboardPage from "@/pages/DashboardPage";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Fleet Dashboard — TransitOps" },
      {
        name: "description",
        content: "Real-time KPIs, utilization, and revenue signals across your fleet.",
      },
    ],
  }),
  component: DashboardPage,
});
