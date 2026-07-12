export const UserRole = {
  FLEET_MANAGER: "Fleet Manager",
  DRIVER: "Driver",
  SAFETY_OFFICER: "Safety Officer",
  FINANCIAL_ANALYST: "Financial Analyst",
} as const;
export type UserRole = (typeof UserRole)[keyof typeof UserRole];

export const VehicleStatus = {
  AVAILABLE: "Available",
  ON_TRIP: "On Trip",
  IN_SHOP: "In Shop",
  RETIRED: "Retired",
} as const;
export type VehicleStatus = (typeof VehicleStatus)[keyof typeof VehicleStatus];

export const DriverStatus = {
  AVAILABLE: "Available",
  ON_TRIP: "On Trip",
  OFF_DUTY: "Off Duty",
  SUSPENDED: "Suspended",
} as const;
export type DriverStatus = (typeof DriverStatus)[keyof typeof DriverStatus];

export const TripStatus = {
  DRAFT: "Draft",
  DISPATCHED: "Dispatched",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
} as const;
export type TripStatus = (typeof TripStatus)[keyof typeof TripStatus];

export const MaintenanceStatus = {
  OPEN: "Open",
  CLOSED: "Closed",
} as const;
export type MaintenanceStatus = (typeof MaintenanceStatus)[keyof typeof MaintenanceStatus];

export const API_BASE_URL = "http://localhost:8000/api";