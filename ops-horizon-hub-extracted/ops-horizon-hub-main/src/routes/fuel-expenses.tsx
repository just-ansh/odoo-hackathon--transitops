import { createFileRoute } from "@tanstack/react-router";
import FuelExpensesPage from "@/pages/FuelExpensesPage";

export const Route = createFileRoute("/fuel-expenses")({
  head: () => ({
    meta: [
      { title: "Fuel & Expenses — TransitOps" },
      { name: "description", content: "Fueling and operating cost logs." },
    ],
  }),
  component: FuelExpensesPage,
});
