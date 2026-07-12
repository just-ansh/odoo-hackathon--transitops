"""
TransitOps FastAPI Web App Server (main.py)
------------------------------------------
Wraps transaction business logic functions into standard API routes,
validating inputs using Pydantic models.

Author: Developer 1 (Senior Database Architect & Backend Engineer)
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import database

app = FastAPI(
    title="TransitOps API",
    description="Smart Transport Operations Platform API for Hackathon",
    version="1.0.0"
)

# =====================================================================
# PYDANTIC SCHEMAS FOR API INPUTS
# =====================================================================

class DispatchTripRequest(BaseModel):
    vehicle_id: int = Field(..., description="ID of the vehicle to dispatch")
    driver_id: int = Field(..., description="ID of the driver to dispatch")
    cargo_weight: float = Field(..., gt=0, description="Cargo weight in kg")
    source: str = Field(..., min_length=2, max_length=150, description="Source location")
    destination: str = Field(..., min_length=2, max_length=150, description="Destination location")
    planned_distance: float = Field(..., gt=0, description="Planned trip distance in miles/km")
    revenue: float = Field(default=0.0, ge=0, description="Projected/agreed revenue for the trip")

class CompleteTripRequest(BaseModel):
    trip_id: int = Field(..., description="ID of the trip to complete")
    final_odometer: float = Field(..., description="Final odometer reading of the vehicle")
    fuel_consumed: float = Field(..., ge=0, description="Liters of fuel consumed during the trip")

class OpenMaintenanceRequest(BaseModel):
    vehicle_id: int = Field(..., description="ID of the vehicle to place in maintenance")
    description: str = Field(..., min_length=5, description="Details of the maintenance log")


# =====================================================================
# API ROUTE ENDPOINTS
# =====================================================================

@app.post("/api/dispatch", status_code=status.HTTP_201_CREATED)
def api_dispatch_trip(payload: DispatchTripRequest):
    """
    Dispatches a new trip, locking the vehicle and driver to verify capacity
    and status availability.
    """
    try:
        trip = database.dispatch_trip(
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            cargo_weight=payload.cargo_weight,
            source=payload.source,
            destination=payload.destination,
            planned_distance=payload.planned_distance,
            revenue=payload.revenue
        )
        return {"message": "Trip successfully dispatched", "trip": trip}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (database.ResourceUnavailableError, database.CapacityExceededError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal database error: {e}")


@app.post("/api/complete", status_code=status.HTTP_200_OK)
def api_complete_trip(payload: CompleteTripRequest):
    """
    Completes a dispatched trip, updates final odometer and fuel consumption,
    and returns both driver and vehicle back to 'Available' status.
    """
    try:
        trip = database.complete_trip(
            trip_id=payload.trip_id,
            final_odometer=payload.final_odometer,
            fuel_consumed=payload.fuel_consumed
        )
        return {"message": "Trip successfully completed", "trip": trip}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (database.InvalidOdometerError, database.InvalidStatusTransitionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal database error: {e}")


@app.post("/api/maintenance", status_code=status.HTTP_201_CREATED)
def api_open_maintenance(payload: OpenMaintenanceRequest):
    """
    Puts a vehicle in maintenance ('In Shop') and opens a new maintenance log entry.
    """
    try:
        log = database.open_maintenance(
            vehicle_id=payload.vehicle_id,
            description=payload.description
        )
        return {"message": "Vehicle successfully sent to shop", "maintenance_log": log}
    except database.EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except database.ResourceUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal database error: {e}")


@app.get("/api/roi", status_code=status.HTTP_200_OK)
def api_get_fleet_roi():
    """
    Calculates and returns the global fleet-wide ROI metrics.
    """
    try:
        roi_data = database.get_fleet_roi()
        return {"roi_metrics": roi_data}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to calculate ROI: {e}")


@app.get("/api/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Verifies API health and tests database connectivity.
    """
    try:
        # Check connection is active
        conn = database.get_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Database connection unhealthy: {e}"
        )
