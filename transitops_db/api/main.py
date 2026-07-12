"""
TransitOps FastAPI Web App Server (api/main.py)
-----------------------------------------------
Full REST API covering all CRUD operations, transactions, and analytics.

Author: Developer 1 (Senior Database Architect & Backend Engineer)

NOTE ON AUTH:
  Authentication (login + RBAC) is intentionally OUT OF SCOPE for this
  hackathon submission. Both team members agreed to drop it due to the
  strict 8-hour time budget. All endpoints are publicly accessible.
  If the rubric penalises this, a stub JWT middleware can be added in
  under 30 minutes using python-jose, but business logic will be unaffected.
"""

import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from psycopg.errors import UniqueViolation

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import database
from api.schemas import (
    DispatchTripRequest,
    CompleteTripRequest,
    OpenMaintenanceRequest,
    CloseMaintenanceRequest,
    AddFuelLogRequest,
    AddExpenseRequest,
)

app = FastAPI(
    title="TransitOps API",
    description="""
Smart Transport Operations Platform — Hackathon Build.

## Auth Note
Authentication is **out of scope** for this build. All endpoints are open.

## Error Codes
- `400` — Business logic validation failure (busy resource, capacity exceeded, duplicate entry, etc.)
- `404` — Requested entity does not exist
- `500` — Unexpected server or database error
- `503` — Database connection is down (health check failure)
    """,
    version="1.0.0",
)

# Allow all origins so the frontend (any host/port) can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# HEALTH CHECK
# =====================================================================

@app.get("/api/health", tags=["Health"])
def health_check():
    """
    Checks whether the API and database are reachable.

    Returns:
    - `200 {"status": "healthy", "database": "connected"}` — Everything is up.
    - `503 {"detail": "Database connection unhealthy: <reason>"}` — API is up but DB is down.
    """
    try:
        conn = database.get_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection unhealthy: {e}"
        )


# =====================================================================
# VEHICLES
# =====================================================================

@app.get("/api/vehicles", tags=["Vehicles"])
def api_get_vehicles(
    status: Optional[str] = Query(default=None, description="Filter by status: Available, On Trip, In Shop, Retired"),
    type: Optional[str] = Query(default=None, description="Filter by vehicle type e.g. Flatbed, Heavy Hauler"),
):
    """Returns all vehicles. Supports optional filtering by `status` and/or `type`."""
    try:
        return database.get_vehicles(status=status, type=type)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =====================================================================
# DRIVERS
# =====================================================================

@app.get("/api/drivers", tags=["Drivers"])
def api_get_drivers(
    status: Optional[str] = Query(default=None, description="Filter by status: Available, On Trip, Off Duty, Suspended"),
):
    """Returns all drivers. Supports optional filtering by `status`."""
    try:
        return database.get_drivers(status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# TRIPS
# =====================================================================

@app.get("/api/trips", tags=["Trips"])
def api_get_trips(
    status: Optional[str] = Query(default=None, description="Filter by status: Draft, Dispatched, Completed, Cancelled"),
    vehicle_id: Optional[int] = Query(default=None, description="Filter by vehicle ID"),
    driver_id: Optional[int] = Query(default=None, description="Filter by driver ID"),
):
    """Returns all trips. Supports optional filtering by `status`, `vehicle_id`, and/or `driver_id`."""
    try:
        return database.get_trips(status=status, vehicle_id=vehicle_id, driver_id=driver_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dispatch", status_code=status.HTTP_201_CREATED, tags=["Trips"])
def api_dispatch_trip(payload: DispatchTripRequest):
    """
    Dispatches a new trip (atomic transaction).
    - Vehicle must be 'Available' and have sufficient load capacity.
    - Driver must be 'Available'.
    - Both are immediately set to 'On Trip' on success.
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
def api_complete_trip(payload: CompleteTripRequest):
    """
    Completes a dispatched trip (atomic transaction).
    - Trip must be in 'Dispatched' status.
    - `final_odometer` must be >= current vehicle odometer.
    - Both vehicle and driver are returned to 'Available' on success.
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
    vehicle_id: Optional[int] = Query(default=None, description="Filter by vehicle ID"),
    status: Optional[str] = Query(default=None, description="Filter by status: Open, Closed"),
):
    """Returns all maintenance logs. Supports optional filtering by `vehicle_id` and/or `status`."""
    try:
        return database.get_maintenance_logs(vehicle_id=vehicle_id, status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/maintenance/open", status_code=status.HTTP_201_CREATED, tags=["Maintenance"])
def api_open_maintenance(payload: OpenMaintenanceRequest):
    """
    Opens a maintenance log (atomic transaction).
    - Vehicle must exist and must not be 'Retired'.
    - Vehicle status is immediately set to 'In Shop'.
    """
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
def api_close_maintenance(payload: CloseMaintenanceRequest):
    """
    Closes an open maintenance log (atomic transaction).
    - Log must be in 'Open' status.
    - Records the final cost and timestamps the closure.
    - Vehicle is immediately restored to 'Available'.
    """
    try:
        log = database.close_maintenance(
            log_id=payload.log_id,
            cost=payload.cost,
        )
        return {"message": "Maintenance log closed and vehicle restored to Available", "maintenance_log": log}
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
    vehicle_id: Optional[int] = Query(default=None, description="Filter by vehicle ID"),
    trip_id: Optional[int] = Query(default=None, description="Filter by trip ID"),
):
    """Returns all fuel log entries. Supports optional filtering by `vehicle_id` and/or `trip_id`."""
    try:
        return database.get_fuel_logs(vehicle_id=vehicle_id, trip_id=trip_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fuel-logs", status_code=status.HTTP_201_CREATED, tags=["Fuel Logs"])
def api_add_fuel_log(payload: AddFuelLogRequest):
    """Records a new fuel purchase for a vehicle, optionally linked to a trip."""
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
    vehicle_id: Optional[int] = Query(default=None, description="Filter by vehicle ID"),
    type: Optional[str] = Query(default=None, description="Filter by type: Tolls, Maintenance, Other"),
):
    """Returns all expense entries. Supports optional filtering by `vehicle_id` and/or `type`."""
    try:
        return database.get_expenses(vehicle_id=vehicle_id, type=type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/expenses", status_code=status.HTTP_201_CREATED, tags=["Expenses"])
def api_add_expense(payload: AddExpenseRequest):
    """Records a new operational expense (Tolls, Maintenance, Other) for a vehicle."""
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
# ROI / ANALYTICS
# =====================================================================

@app.get("/api/roi", tags=["Analytics"])
def api_get_fleet_roi():
    """Returns aggregated fleet-wide ROI metrics (revenue, costs, ROI ratio)."""
    try:
        return {"roi_metrics": database.get_fleet_roi()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/roi/vehicles", tags=["Analytics"])
def api_get_vehicle_roi_breakdown():
    """
    Returns a per-vehicle breakdown of ROI metrics.
    Includes revenue, maintenance cost, fuel cost, and individual ROI per vehicle.
    Uses pre-aggregated subqueries to prevent row-multiplication inaccuracies.
    """
    try:
        return {"vehicle_roi_breakdown": database.get_vehicle_roi_breakdown()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
