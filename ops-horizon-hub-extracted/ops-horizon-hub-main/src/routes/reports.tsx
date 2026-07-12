import { createFileRoute } from "@tanstack/react-router";
import ReportsPage from "@/pages/ReportsPage";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Reports — TransitOps" },
      { name: "description", content: "Fleet ROI, fuel efficiency and utilization reports." },
    ],
  }),
  component: ReportsPage,
});
