import { UserRole, VehicleStatus, DriverStatus, TripStatus, MaintenanceStatus } from "@/lib/constants";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
}

export interface Vehicle {
  id: number;
  registration_number: string;
  name_model: string;
  type: string;
  max_load_capacity: number;
  odometer: number;
  acquisition_cost: number;
  status: VehicleStatus;
  region: string | null;
}

export interface Driver {
  id: number;
  name: string;
  license_number: string;
  license_category: string;
  license_expiry_date: string; // ISO date
  contact_number: string;
  safety_score: number;
  status: DriverStatus;
}

export interface Trip {
  id: number;
  source: string;
  destination: string;
  vehicle_id: number;
  driver_id: number;
  cargo_weight: number;
  planned_distance: number;
  final_odometer: number | null;
  fuel_consumed: number | null;
  status: TripStatus;
  created_at: string;
  dispatched_at: string | null;
  completed_at: string | null;
}

export interface MaintenanceLog {
  id: number;
  vehicle_id: number;
  description: string;
  cost: number;
  status: MaintenanceStatus;
  created_at: string;
  closed_at: string | null;
}

export interface FuelLog {
  id: number;
  vehicle_id: number;
  liters: number;
  cost: number;
  date: string;
}

export interface Expense {
  id: number;
  vehicle_id: number;
  category: string;
  amount: number;
  date: string;
  notes: string | null;
}

export interface DashboardKPIs {
  active_vehicles: number;
  available_vehicles: number;
  vehicles_in_maintenance: number;
  active_trips: number;
  pending_trips: number;
  drivers_on_duty: number;
  fleet_utilization_pct: number;
}