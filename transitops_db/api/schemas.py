"""
TransitOps API Schemas (api/schemas.py)
--------------------------------------
Pydantic models for all request payloads. Used by FastAPI for automatic
input validation and OpenAPI documentation.

Author: Developer 1 (Senior Database Architect & Backend Engineer)
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


# =====================================================================
# TRIP SCHEMAS
# =====================================================================

class DispatchTripRequest(BaseModel):
    vehicle_id: int = Field(..., description="ID of the vehicle to dispatch")
    driver_id: int = Field(..., description="ID of the driver to dispatch")
    cargo_weight: float = Field(..., gt=0, description="Cargo weight in kg")
    source: str = Field(..., min_length=2, max_length=150, description="Source location")
    destination: str = Field(..., min_length=2, max_length=150, description="Destination location")
    planned_distance: float = Field(..., gt=0, description="Planned trip distance in km")
    revenue: float = Field(default=0.0, ge=0, description="Agreed revenue for the trip")


class CompleteTripRequest(BaseModel):
    trip_id: int = Field(..., description="ID of the dispatched trip to complete")
    final_odometer: float = Field(..., ge=0, description="Final odometer reading of the vehicle (km)")
    fuel_consumed_liters: float = Field(..., ge=0, description="Total liters of fuel consumed during the trip")


# =====================================================================
# MAINTENANCE SCHEMAS
# =====================================================================

class OpenMaintenanceRequest(BaseModel):
    vehicle_id: int = Field(..., description="ID of the vehicle to place in maintenance")
    description: str = Field(..., min_length=5, description="Description of the maintenance work to be done")


class CloseMaintenanceRequest(BaseModel):
    log_id: int = Field(..., description="ID of the open maintenance log to close")
    cost: float = Field(..., ge=0, description="Final cost of the maintenance work")


# =====================================================================
# FUEL LOG SCHEMAS
# =====================================================================

class AddFuelLogRequest(BaseModel):
    vehicle_id: int = Field(..., description="ID of the vehicle that was fueled")
    liters: float = Field(..., gt=0, description="Amount of fuel added in liters")
    cost: float = Field(..., ge=0, description="Total cost of the fuel purchase")
    logged_date: date = Field(..., description="Date of the fuel purchase (YYYY-MM-DD)")
    trip_id: Optional[int] = Field(default=None, description="Optional: ID of the trip this fuel was for")


# =====================================================================
# EXPENSE SCHEMAS
# =====================================================================

class AddExpenseRequest(BaseModel):
    vehicle_id: int = Field(..., description="ID of the vehicle this expense is for")
    type: str = Field(..., description="Expense type: 'Tolls', 'Maintenance', or 'Other'")
    amount: float = Field(..., ge=0, description="Expense amount")
    description: str = Field(..., min_length=3, description="Description of the expense")
    logged_date: date = Field(..., description="Date the expense was incurred (YYYY-MM-DD)")
