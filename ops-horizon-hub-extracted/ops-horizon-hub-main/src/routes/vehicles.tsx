import { createFileRoute } from "@tanstack/react-router";
import VehiclesPage from "@/pages/VehiclesPage";

export const Route = createFileRoute("/vehicles")({
  head: () => ({
    meta: [
      { title: "Vehicles — TransitOps" },
      { name: "description", content: "Vehicle registry, capacity, and lifecycle." },
    ],
  }),
  component: VehiclesPage,
});
