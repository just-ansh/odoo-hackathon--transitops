import type { UserRole, VehicleStatus, DriverStatus, TripStatus, MaintenanceStatus } from "@/lib/constants";

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
  license_expiry_date: string;
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
  fuel_consumed_liters: number | null;
  revenue: number;
  status: TripStatus;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
}

export interface MaintenanceLog {
  id: number;
  vehicle_id: number;
  description: string;
  cost: number;
  status: MaintenanceStatus;
  logged_at: string;
  closed_at: string | null;
}

export interface FuelLog {
  id: number;
  vehicle_id: number;
  liters: number;
  cost: number;
  logged_date: string;
  trip_id: number | null;
}

export interface Expense {
  id: number;
  vehicle_id: number;
  type: 'Tolls' | 'Maintenance' | 'Other';
  amount: number;
  description: string;
  logged_date: string;
}