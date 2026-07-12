import axios from "axios";
import { API_BASE_URL } from "./constants";
import { useAuthStore } from "@/store/authStore";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Cache GET requests and fallback on failure
api.interceptors.response.use(
  (response) => {
    if (response.config.method === 'get') {
      const cacheKey = `api_cache:${response.config.url}?${JSON.stringify(response.config.params || {})}`;
      try {
        localStorage.setItem(cacheKey, JSON.stringify(response.data));
      } catch (e) {
        // ignore storage errors
      }
    }
    return response;
  },
  (error) => {
    const config = error.config;
    if (config && config.method === 'get') {
      const cacheKey = `api_cache:${config.url}?${JSON.stringify(config.params || {})}`;
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        console.warn(`Fallback to offline cache for ${config.url}`);
        return Promise.resolve({
          data: JSON.parse(cached),
          status: 200,
          statusText: 'OK (Cached)',
          headers: {},
          config,
        });
      }
    }
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ---------- AUTH ----------
export const login = (email: string, password: string) =>
  api.post("/auth/login", { email, password });
export const register = (email: string, password: string, role: string) =>
  api.post("/auth/register", { email, password, role });

// ---------- VEHICLES ----------
export const getVehicles = (params?: { status?: string; type?: string }) =>
  api.get("/vehicles", { params });
export const createVehicle = (data: any) => api.post("/vehicles", data);
export const updateVehicle = (id: number, data: any) => api.patch(`/vehicles/${id}`, data);
export const deleteVehicle = (id: number) => api.delete(`/vehicles/${id}`);

// ---------- DRIVERS ----------
export const getDrivers = (params?: { status?: string }) =>
  api.get("/drivers", { params });
export const createDriver = (data: any) => api.post("/drivers", data);
export const updateDriver = (id: number, data: any) => api.patch(`/drivers/${id}`, data);
export const deleteDriver = (id: number) => api.delete(`/drivers/${id}`);

// ---------- TRIPS ----------
export const getTrips = (params?: { status?: string; vehicle_id?: number; driver_id?: number }) =>
  api.get("/trips", { params });
export const createTrip = (data: any) => api.post("/trips", data);
export const dispatchTrip = (id: number) => api.post(`/trips/${id}/dispatch`);
export const completeTrip = (id: number, data: { final_odometer: number; fuel_consumed_liters: number }) =>
  api.post(`/trips/${id}/complete`, { trip_id: id, ...data });
export const cancelTrip = (id: number) => api.post(`/trips/${id}/cancel`);

// ---------- MAINTENANCE ----------
export const getMaintenanceLogs = (params?: { vehicle_id?: number; status?: string }) =>
  api.get("/maintenance", { params });
export const openMaintenanceLog = (data: { vehicle_id: number; description: string }) =>
  api.post("/maintenance/open", data);
export const closeMaintenanceLog = (id: number, cost: number) =>
  api.post("/maintenance/close", { log_id: id, cost });

// ---------- FUEL & EXPENSES ----------
export const getFuelLogs = (params?: { vehicle_id?: number; trip_id?: number }) =>
  api.get("/fuel-logs", { params });
export const createFuelLog = (data: { vehicle_id: number; liters: number; cost: number; logged_date: string; trip_id?: number }) =>
  api.post("/fuel-logs", data);
export const getExpenses = (params?: { vehicle_id?: number; type?: string }) =>
  api.get("/expenses", { params });
export const createExpense = (data: { vehicle_id: number; type: string; amount: number; description: string; logged_date: string }) =>
  api.post("/expenses", data);

// ---------- DASHBOARD & REPORTS ----------
export const getDashboardKPIs = (params?: { type?: string; status?: string; region?: string }) =>
  api.get("/dashboard", { params });
export const getFleetRoi = () => api.get("/roi");
export const getVehicleRoiBreakdown = () => api.get("/roi/vehicles");