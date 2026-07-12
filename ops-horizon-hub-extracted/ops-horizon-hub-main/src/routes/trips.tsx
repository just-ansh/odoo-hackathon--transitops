import { createFileRoute } from "@tanstack/react-router";
import TripsPage from "@/pages/TripsPage";

export const Route = createFileRoute("/trips")({
  head: () => ({
    meta: [
      { title: "Trips — TransitOps" },
      { name: "description", content: "Dispatch, monitor, and close trips end-to-end." },
    ],
  }),
  component: TripsPage,
});
