import { createFileRoute } from "@tanstack/react-router";
import DriversPage from "@/pages/DriversPage";

export const Route = createFileRoute("/drivers")({
  head: () => ({
    meta: [
      { title: "Drivers — TransitOps" },
      { name: "description", content: "Driver registry, license and safety tracking." },
    ],
  }),
  component: DriversPage,
});
