"""
TransitOps API Schemas (api/schemas.py)
--------------------------------------
Pydantic models for all request payloads. Used by FastAPI for automatic
input validation and OpenAPI documentation.

Author: Developer 1 (Senior Database Architect & Backend Engineer)
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, EmailStr


# =====================================================================
# AUTH SCHEMAS
# =====================================================================

class LoginRequest(BaseModel):
    email: str = Field(..., description="Registered user email address")
    password: str = Field(..., min_length=6, description="Account password")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address to register")
    password: str = Field(..., min_length=6, description="Account password")
    role: str = Field(..., description="One of: 'Fleet Manager', 'Driver', 'Safety Officer', 'Financial Analyst'")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str



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


# =====================================================================
# VEHICLE CRUD SCHEMAS
# =====================================================================

class VehicleCreate(BaseModel):
    registration_number: str = Field(..., description="Unique registration plate number")
    name_model: str = Field(..., min_length=2, description="Brand and model name")
    type: str = Field(..., description="Vehicle type, e.g. Flatbed, Heavy Hauler")
    max_load_capacity: float = Field(..., gt=0, description="Max load capacity in kg")
    odometer: float = Field(default=0.0, ge=0, description="Initial odometer reading in km")
    acquisition_cost: float = Field(..., ge=0, description="Cost of acquiring the vehicle")
    status: str = Field(default="Available", description="Vehicle status")
    region: Optional[str] = Field(default=None, description="Operational region")


class VehicleUpdate(BaseModel):
    registration_number: Optional[str] = Field(default=None)
    name_model: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    max_load_capacity: Optional[float] = Field(default=None, gt=0)
    odometer: Optional[float] = Field(default=None, ge=0)
    acquisition_cost: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None)
    region: Optional[str] = Field(default=None)


# =====================================================================
# DRIVER CRUD SCHEMAS
# =====================================================================

class DriverCreate(BaseModel):
    name: str = Field(..., min_length=2, description="Full name of driver")
    license_number: str = Field(..., description="Unique driver license number")
    license_category: str = Field(..., description="License category, e.g. Class A CDL")
    license_expiry_date: date = Field(..., description="Driver license expiry date YYYY-MM-DD")
    contact_number: str = Field(..., description="Driver contact phone number")
    safety_score: float = Field(default=100.0, ge=0, le=100, description="Driver safety score (0-100)")
    status: str = Field(default="Available", description="Driver status")


class DriverUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    license_number: Optional[str] = Field(default=None)
    license_category: Optional[str] = Field(default=None)
    license_expiry_date: Optional[date] = Field(default=None)
    contact_number: Optional[str] = Field(default=None)
    safety_score: Optional[float] = Field(default=None, ge=0, le=100)
    status: Optional[str] = Field(default=None)


# =====================================================================
# TRIP CRUD SCHEMAS
# =====================================================================

class TripCreate(BaseModel):
    source: str = Field(..., min_length=2, max_length=150)
    destination: str = Field(..., min_length=2, max_length=150)
    vehicle_id: int = Field(...)
    driver_id: int = Field(...)
    cargo_weight: float = Field(..., gt=0)
    planned_distance: float = Field(..., gt=0)
    revenue: float = Field(default=0.0, ge=0)
    status: str = Field(default="Draft")

