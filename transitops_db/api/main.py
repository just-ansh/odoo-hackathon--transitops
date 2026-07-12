"""
TransitOps FastAPI Web App Server (api/main.py)
-----------------------------------------------
Full REST API with JWT authentication and role-based access control (RBAC).

Auth Flow:
  1. POST /api/auth/login  → receive JWT token
  2. Add header to all requests: Authorization: Bearer <token>
  3. Unauthorized → 401.  Wrong role → 403.

RBAC Matrix:
  Fleet Manager    → full access to all endpoints
  Driver           → GET vehicles/drivers/trips, POST /api/complete
  Safety Officer   → GET vehicles/drivers/trips/maintenance,
                     POST /api/maintenance/open, POST /api/maintenance/close
  Financial Analyst→ GET trips/fuel-logs/expenses/roi,
                     POST /api/fuel-logs, POST /api/expenses

Author: Developer 1 (Senior Backend Engineer)
"""

import os
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from psycopg.errors import UniqueViolation

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import database
from core.auth import (
    require_roles,
    get_current_user,
    FLEET_MANAGER,
    DRIVER,
    SAFETY_OFFICER,
    FINANCIAL_ANALYST,
    ALL_ROLES,
)
from api import auth_routes
from api.schemas import (
    DispatchTripRequest,
    CompleteTripRequest,
    OpenMaintenanceRequest,
    CloseMaintenanceRequest,
    AddFuelLogRequest,
    AddExpenseRequest,
    VehicleCreate,
    VehicleUpdate,
    DriverCreate,
    DriverUpdate,
    TripCreate,
)

app = FastAPI(
    title="TransitOps API",
    description="""
## Smart Transport Operations Platform

### Authentication
All endpoints (except `/api/auth/login` and `/api/health`) require a Bearer token.

1. Call `POST /api/auth/login` with email + password.
2. Copy the returned `access_token`.
3. Click **Authorize** (top-right 🔒) in Swagger UI and paste the token.
4. All subsequent requests will include the token automatically.

### RBAC Roles
| Role | Permissions |
|------|------------|
| Fleet Manager | Full access to all endpoints |
| Driver | View fleet/trips, complete own trips |
| Safety Officer | View fleet/trips, manage maintenance |
| Financial Analyst | View trips/roi, manage fuel logs & expenses |
    """,
    version="2.0.0",
)

# Allow frontend on any origin/port to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register auth router (login + me — no RBAC on these)
app.include_router(auth_routes.router)


# =====================================================================
# HEALTH CHECK (public — no auth required)
# =====================================================================

@app.get("/api/health", tags=["Health"])
def health_check():
    """
    Public endpoint. Checks API and database connectivity.
    - `200` → healthy
    - `503` → API up but database is unreachable
    """
    try:
        conn = database.get_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection unhealthy: {e}",
        )


# =====================================================================
# VEHICLES  (all roles can read)
# =====================================================================

@app.get("/api/vehicles", tags=["Vehicles"])
def api_get_vehicles(
    status_filter: Optional[str] = Query(default=None, alias="status",
        description="Filter: Available | On Trip | In Shop | Retired"),
    type: Optional[str] = Query(default=None,
        description="Filter by vehicle type e.g. Flatbed, Heavy Hauler"),
    _user: dict = Depends(require_roles(*ALL_ROLES)),
):
    """Returns all vehicles. Any authenticated role may call this."""
    try:
        return database.get_vehicles(status=status_filter, type=type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# DRIVERS  (all roles can read)
# =====================================================================

@app.get("/api/drivers", tags=["Drivers"])
def api_get_drivers(
    status_filter: Optional[str] = Query(default=None, alias="status",
        description="Filter: Available | On Trip | Off Duty | Suspended"),
    _user: dict = Depends(require_roles(*ALL_ROLES)),
):
    """Returns all drivers. Any authenticated role may call this."""
    try:
        return database.get_drivers(status=status_filter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# TRIPS
# =====================================================================

@app.get("/api/trips", tags=["Trips"])
def api_get_trips(
    status_filter: Optional[str] = Query(default=None, alias="status",
        description="Filter: Draft | Dispatched | Completed | Cancelled"),
    vehicle_id: Optional[int] = Query(default=None),
    driver_id: Optional[int] = Query(default=None),
    _user: dict = Depends(require_roles(*ALL_ROLES)),
):
    """Returns all trips. Any authenticated role may call this."""
    try:
        return database.get_trips(
            status=status_filter, vehicle_id=vehicle_id, driver_id=driver_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dispatch", status_code=201, tags=["Trips"])
def api_dispatch_trip(
    payload: DispatchTripRequest,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """
    **Fleet Manager only.**
    Dispatches a new trip. Vehicle and driver must both be 'Available'.
    """
    try:
        trip = database.dispatch_trip(
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            cargo_weight=payload.cargo_weight,
            source=payload.source,
            destination=payload.destination,
            planned_distance=payload.planned_distance,
            revenue=payload.revenue,
        )
        return {"message": "Trip successfully dispatched", "trip": trip}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (database.ResourceUnavailableError, database.CapacityExceededError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/complete", tags=["Trips"])
def api_complete_trip(
    payload: CompleteTripRequest,
    _user: dict = Depends(require_roles(FLEET_MANAGER, DRIVER)),
):
    """
    **Fleet Manager or Driver.**
    Completes a dispatched trip. Records final odometer and fuel consumed.
    """
    try:
        trip = database.complete_trip(
            trip_id=payload.trip_id,
            final_odometer=payload.final_odometer,
            fuel_consumed_liters=payload.fuel_consumed_liters,
        )
        return {"message": "Trip successfully completed", "trip": trip}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (database.InvalidOdometerError, database.InvalidStatusTransitionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# MAINTENANCE
# =====================================================================

@app.get("/api/maintenance", tags=["Maintenance"])
def api_get_maintenance_logs(
    vehicle_id: Optional[int] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status",
        description="Filter: Open | Closed"),
    _user: dict = Depends(require_roles(FLEET_MANAGER, SAFETY_OFFICER)),
):
    """**Fleet Manager or Safety Officer.** Returns all maintenance logs."""
    try:
        return database.get_maintenance_logs(
            vehicle_id=vehicle_id, status=status_filter
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/maintenance/open", status_code=201, tags=["Maintenance"])
def api_open_maintenance(
    payload: OpenMaintenanceRequest,
    _user: dict = Depends(require_roles(FLEET_MANAGER, SAFETY_OFFICER)),
):
    """**Fleet Manager or Safety Officer.** Opens a maintenance log. Sets vehicle to 'In Shop'."""
    try:
        log = database.open_maintenance(
            vehicle_id=payload.vehicle_id,
            description=payload.description,
        )
        return {"message": "Vehicle successfully sent to shop", "maintenance_log": log}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except database.ResourceUnavailableError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/maintenance/close", tags=["Maintenance"])
def api_close_maintenance(
    payload: CloseMaintenanceRequest,
    _user: dict = Depends(require_roles(FLEET_MANAGER, SAFETY_OFFICER)),
):
    """**Fleet Manager or Safety Officer.** Closes maintenance log. Restores vehicle to 'Available'."""
    try:
        log = database.close_maintenance(log_id=payload.log_id, cost=payload.cost)
        return {
            "message": "Maintenance log closed and vehicle restored to Available",
            "maintenance_log": log,
        }
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except database.InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# FUEL LOGS
# =====================================================================

@app.get("/api/fuel-logs", tags=["Fuel Logs"])
def api_get_fuel_logs(
    vehicle_id: Optional[int] = Query(default=None),
    trip_id: Optional[int] = Query(default=None),
    _user: dict = Depends(require_roles(FLEET_MANAGER, FINANCIAL_ANALYST)),
):
    """**Fleet Manager or Financial Analyst.** Returns all fuel log entries."""
    try:
        return database.get_fuel_logs(vehicle_id=vehicle_id, trip_id=trip_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fuel-logs", status_code=201, tags=["Fuel Logs"])
def api_add_fuel_log(
    payload: AddFuelLogRequest,
    _user: dict = Depends(require_roles(FLEET_MANAGER, FINANCIAL_ANALYST)),
):
    """**Fleet Manager or Financial Analyst.** Records a fuel purchase for a vehicle."""
    try:
        log = database.add_fuel_log(
            vehicle_id=payload.vehicle_id,
            liters=payload.liters,
            cost=payload.cost,
            logged_date=str(payload.logged_date),
            trip_id=payload.trip_id,
        )
        return {"message": "Fuel log recorded", "fuel_log": log}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# EXPENSES
# =====================================================================

@app.get("/api/expenses", tags=["Expenses"])
def api_get_expenses(
    vehicle_id: Optional[int] = Query(default=None),
    type: Optional[str] = Query(default=None,
        description="Filter: Tolls | Maintenance | Other"),
    _user: dict = Depends(require_roles(FLEET_MANAGER, FINANCIAL_ANALYST)),
):
    """**Fleet Manager or Financial Analyst.** Returns all expense entries."""
    try:
        return database.get_expenses(vehicle_id=vehicle_id, type=type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/expenses", status_code=201, tags=["Expenses"])
def api_add_expense(
    payload: AddExpenseRequest,
    _user: dict = Depends(require_roles(FLEET_MANAGER, FINANCIAL_ANALYST)),
):
    """**Fleet Manager or Financial Analyst.** Records an operational expense."""
    try:
        expense = database.add_expense(
            vehicle_id=payload.vehicle_id,
            type=payload.type,
            amount=payload.amount,
            description=payload.description,
            logged_date=str(payload.logged_date),
        )
        return {"message": "Expense recorded", "expense": expense}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UniqueViolation:
        raise HTTPException(status_code=400, detail="A duplicate entry violates a unique constraint.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# ANALYTICS / ROI
# =====================================================================

@app.get("/api/roi", tags=["Analytics"])
def api_get_fleet_roi(
    _user: dict = Depends(require_roles(FLEET_MANAGER, FINANCIAL_ANALYST)),
):
    """**Fleet Manager or Financial Analyst.** Fleet-wide aggregated ROI metrics."""
    try:
        return {"roi_metrics": database.get_fleet_roi()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/roi/vehicles", tags=["Analytics"])
def api_get_vehicle_roi_breakdown(
    _user: dict = Depends(require_roles(FLEET_MANAGER, FINANCIAL_ANALYST)),
):
    """**Fleet Manager or Financial Analyst.** Per-vehicle ROI breakdown."""
    try:
        return {"vehicle_roi_breakdown": database.get_vehicle_roi_breakdown()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# VEHICLES CRUD ENDPOINTS
# =====================================================================

@app.post("/api/vehicles", status_code=201, tags=["Vehicles"])
def api_create_vehicle(
    payload: VehicleCreate,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """**Fleet Manager only.** Adds a new vehicle to the fleet registry."""
    try:
        vehicle = database.create_vehicle(
            registration_number=payload.registration_number,
            name_model=payload.name_model,
            type=payload.type,
            max_load_capacity=payload.max_load_capacity,
            odometer=payload.odometer,
            acquisition_cost=payload.acquisition_cost,
            status=payload.status,
            region=payload.region
        )
        return {"message": "Vehicle successfully registered", "vehicle": vehicle}
    except database.DuplicateEntryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/vehicles/{vehicle_id}", tags=["Vehicles"])
def api_update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """**Fleet Manager only.** Updates an existing vehicle's fields."""
    try:
        updates = payload.model_dump(exclude_unset=True)
        vehicle = database.update_vehicle(vehicle_id, updates)
        return {"message": "Vehicle updated successfully", "vehicle": vehicle}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except database.DuplicateEntryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/vehicles/{vehicle_id}", tags=["Vehicles"])
def api_delete_vehicle(
    vehicle_id: int,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """**Fleet Manager only.** Deletes a vehicle from the fleet registry."""
    try:
        database.delete_vehicle(vehicle_id)
        return {"message": "Vehicle deleted successfully"}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# DRIVERS CRUD ENDPOINTS
# =====================================================================

@app.post("/api/drivers", status_code=201, tags=["Drivers"])
def api_create_driver(
    payload: DriverCreate,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """**Fleet Manager only.** Adds a new driver profile."""
    try:
        driver = database.create_driver(
            name=payload.name,
            license_number=payload.license_number,
            license_category=payload.license_category,
            license_expiry_date=str(payload.license_expiry_date),
            contact_number=payload.contact_number,
            safety_score=payload.safety_score,
            status=payload.status
        )
        return {"message": "Driver profile created successfully", "driver": driver}
    except database.DuplicateEntryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/drivers/{driver_id}", tags=["Drivers"])
def api_update_driver(
    driver_id: int,
    payload: DriverUpdate,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """**Fleet Manager only.** Updates an existing driver's profile fields."""
    try:
        updates = payload.model_dump(exclude_unset=True)
        if "license_expiry_date" in updates and updates["license_expiry_date"] is not None:
            updates["license_expiry_date"] = str(updates["license_expiry_date"])
        driver = database.update_driver(driver_id, updates)
        return {"message": "Driver profile updated successfully", "driver": driver}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except database.DuplicateEntryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/drivers/{driver_id}", tags=["Drivers"])
def api_delete_driver(
    driver_id: int,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """**Fleet Manager only.** Deletes a driver profile."""
    try:
        database.delete_driver(driver_id)
        return {"message": "Driver profile deleted successfully"}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# TRIPS CREATION & LIFECYCLE ENDPOINTS
# =====================================================================

@app.post("/api/trips", status_code=201, tags=["Trips"])
def api_create_trip(
    payload: TripCreate,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """
    **Fleet Manager only.**
    Creates a new trip (defaults to 'Draft'). If status is 'Dispatched', checks vehicle/driver availability and dispatches.
    """
    try:
        trip = database.create_trip(
            source=payload.source,
            destination=payload.destination,
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            cargo_weight=payload.cargo_weight,
            planned_distance=payload.planned_distance,
            revenue=payload.revenue,
            status=payload.status
        )
        return {"message": "Trip successfully created", "trip": trip}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (database.ResourceUnavailableError, database.CapacityExceededError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trips/{trip_id}/dispatch", tags=["Trips"])
def api_dispatch_existing_trip(
    trip_id: int,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """
    **Fleet Manager only.**
    Dispatches an existing 'Draft' trip. Vehicle and driver must be 'Available'.
    """
    try:
        trip = database.dispatch_trip_by_id(trip_id)
        return {"message": "Trip successfully dispatched", "trip": trip}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (database.ResourceUnavailableError, database.CapacityExceededError, database.InvalidStatusTransitionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trips/{trip_id}/complete", tags=["Trips"])
def api_complete_trip_by_id(
    trip_id: int,
    payload: CompleteTripRequest,
    _user: dict = Depends(require_roles(FLEET_MANAGER, DRIVER)),
):
    """
    **Fleet Manager or Driver.**
    Completes a trip. Records final odometer and fuel consumed.
    """
    try:
        pid = payload.trip_id if payload.trip_id == trip_id else trip_id
        trip = database.complete_trip(
            trip_id=pid,
            final_odometer=payload.final_odometer,
            fuel_consumed_liters=payload.fuel_consumed_liters,
        )
        return {"message": "Trip successfully completed", "trip": trip}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (database.InvalidOdometerError, database.InvalidStatusTransitionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trips/{trip_id}/cancel", tags=["Trips"])
def api_cancel_trip(
    trip_id: int,
    _user: dict = Depends(require_roles(FLEET_MANAGER)),
):
    """
    **Fleet Manager only.**
    Cancels a trip. If the trip was Dispatched, restores vehicle and driver status to 'Available'.
    """
    try:
        trip = database.cancel_trip(trip_id)
        return {"message": "Trip successfully cancelled", "trip": trip}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except database.InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# DASHBOARD / STATISTICS ENDPOINT
# =====================================================================

@app.get("/api/dashboard", tags=["Dashboard"])
def api_get_dashboard_kpis(
    vehicle_type: Optional[str] = Query(default=None, alias="type"),
    status: Optional[str] = Query(default=None),
    region: Optional[str] = Query(default=None),
    _user: dict = Depends(require_roles(*ALL_ROLES)),
):
    """Returns fleet-wide dashboard statistics and KPIs. Any authenticated user may access this."""
    try:
        return database.get_dashboard_kpis(
            vehicle_type=vehicle_type,
            status=status,
            region=region
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

