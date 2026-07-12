"""
TransitOps API Schemas (api/schemas.py)
--------------------------------------
Defines Pydantic models for web request validation.

Author: Developer 1 (Senior Database Architect & Backend Engineer)
"""

from pydantic import BaseModel, Field

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
