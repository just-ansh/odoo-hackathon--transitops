import axios from 'axios';

const baseURL = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api';

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  try {
    const raw = typeof window !== 'undefined' ? window.localStorage.getItem('auth-storage') : null;
    if (raw) {
      const token = JSON.parse(raw)?.state?.token;
      if (token) config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {
    /* ignore */
  }
  return config;
});

const unwrap = <T,>(p: Promise<{ data: T }>): Promise<T> => p.then((r) => r.data);

// Vehicles
export const getVehicles = (params?: { status?: string; type?: string }) =>
  unwrap(api.get('/vehicles', { params }));
export const createVehicle = (data: any) => unwrap(api.post('/vehicles', data));
export const updateVehicle = (id: number, data: any) => unwrap(api.put(`/vehicles/${id}`, data));
export const deleteVehicle = (id: number) => unwrap(api.delete(`/vehicles/${id}`));

// Drivers
export const getDrivers = (params?: { status?: string }) => unwrap(api.get('/drivers', { params }));
export const createDriver = (data: any) => unwrap(api.post('/drivers', data));
export const updateDriver = (id: number, data: any) => unwrap(api.put(`/drivers/${id}`, data));
export const deleteDriver = (id: number) => unwrap(api.delete(`/drivers/${id}`));

// Trips
export const getTrips = (params?: { status?: string; vehicle_id?: number; driver_id?: number }) =>
  unwrap(api.get('/trips', { params }));
export const createTrip = (data: any) => unwrap(api.post('/trips', data));
export const dispatchTrip = (id: number) => unwrap(api.post(`/trips/${id}/dispatch`));
export const completeTrip = (
  id: number,
  data: { final_odometer: number; fuel_consumed_liters: number },
) => unwrap(api.post(`/trips/${id}/complete`, data));
export const cancelTrip = (id: number) => unwrap(api.post(`/trips/${id}/cancel`));

// Maintenance
export const getMaintenanceLogs = (params?: { vehicle_id?: number; status?: string }) =>
  unwrap(api.get('/maintenance', { params }));
export const openMaintenanceLog = (data: { vehicle_id: number; description: string }) =>
  unwrap(api.post('/maintenance', data));
export const closeMaintenanceLog = (id: number, cost: number) =>
  unwrap(api.post(`/maintenance/${id}/close`, { cost }));

// Fuel & expenses
export const getFuelLogs = (params?: { vehicle_id?: number; trip_id?: number }) =>
  unwrap(api.get('/fuel-logs', { params }));
export const createFuelLog = (data: {
  vehicle_id: number;
  liters: number;
  cost: number;
  logged_date: string;
  trip_id?: number;
}) => unwrap(api.post('/fuel-logs', data));

export const getExpenses = (params?: { vehicle_id?: number; type?: string }) =>
  unwrap(api.get('/expenses', { params }));
export const createExpense = (data: {
  vehicle_id: number;
  type: string;
  amount: number;
  description: string;
  logged_date: string;
}) => unwrap(api.post('/expenses', data));

// Reports & dashboard
export const getDashboardKPIs = (params?: { type?: string; status?: string; region?: string }) =>
  unwrap(api.get('/dashboard/kpis', { params }));
export const getFleetRoi = () => unwrap(api.get('/reports/fleet-roi'));
export const getVehicleRoiBreakdown = () => unwrap(api.get('/reports/vehicle-roi'));
