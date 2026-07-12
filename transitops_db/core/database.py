"""
TransitOps Database Utility Module (core/database.py)
-----------------------------------------------------
Handles raw SQL database connections, row-to-dictionary factory configuration,
and atomic business logic transactions using row-level locking.

Author: Developer 1 (Senior Database Architect & Backend Engineer)
"""

import os
import logging
from typing import Dict, Any, List
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

# Configurable Connection String (Defaulting to local PostgreSQL)
DEFAULT_CONN_STRING = "host=localhost dbname=transitops user=postgres password=postgres port=5432"
CONN_STRING = os.getenv("DATABASE_URL", DEFAULT_CONN_STRING)


# =====================================================================
# CUSTOM EXCEPTIONS FOR TRANSACTION SAFETY
# =====================================================================

class TransitOpsDBError(Exception):
    """Base exception for TransitOps database transaction errors."""
    pass

class EntityNotFoundError(TransitOpsDBError):
    """Raised when a vehicle, driver, or trip does not exist."""
    pass

class ResourceUnavailableError(TransitOpsDBError):
    """Raised when a vehicle or driver is not 'Available'."""
    pass

class CapacityExceededError(TransitOpsDBError):
    """Raised when cargo weight exceeds the vehicle's capacity."""
    pass

class InvalidOdometerError(TransitOpsDBError):
    """Raised when odometer values are invalid (e.g. going backward)."""
    pass

class InvalidStatusTransitionError(TransitOpsDBError):
    """Raised when completing a trip that is not currently 'Dispatched'."""
    pass


# =====================================================================
# CONNECTION HELPER
# =====================================================================

def get_connection(conn_string: str = CONN_STRING) -> psycopg.Connection:
    """
    Establishes and returns an active psycopg connection.
    Automatically registers dict_row globally so query outputs are dictionaries.
    """
    try:
        return psycopg.connect(conn_string, row_factory=dict_row)
    except psycopg.Error as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise TransitOpsDBError(f"Database connection failed: {e}")


# =====================================================================
# CORE TRANSACTION: TRIP DISPATCH
# =====================================================================

def dispatch_trip(
    vehicle_id: int,
    driver_id: int,
    cargo_weight: float,
    source: str,
    destination: str,
    planned_distance: float,
    revenue: float = 0.0,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    """
    Dispatches a trip inside an atomic transaction.
    1. Locks and validates vehicle (must exist, status == 'Available', capacity >= cargo_weight).
    2. Locks and validates driver (must exist, status == 'Available').
    3. Inserts the trip as 'Dispatched'.
    4. Updates vehicle and driver status to 'On Trip' atomically.
    """
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                # 1. Lock vehicle and check capacity/status
                cur.execute(
                    "SELECT max_load_capacity, status FROM vehicles WHERE id = %s FOR UPDATE",
                    (vehicle_id,)
                )
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                if vehicle["status"] != "Available":
                    raise ResourceUnavailableError(f"Vehicle {vehicle_id} is '{vehicle['status']}', expected 'Available'.")
                if cargo_weight > float(vehicle["max_load_capacity"]):
                    raise CapacityExceededError(f"Cargo weight {cargo_weight} exceeds vehicle capacity {vehicle['max_load_capacity']}.")

                # 2. Lock driver and check status
                cur.execute(
                    "SELECT status FROM drivers WHERE id = %s FOR UPDATE",
                    (driver_id,)
                )
                driver = cur.fetchone()
                if not driver:
                    raise EntityNotFoundError(f"Driver {driver_id} not found.")
                if driver["status"] != "Available":
                    raise ResourceUnavailableError(f"Driver {driver_id} is '{driver['status']}', expected 'Available'.")

                # 3. Create trip record
                cur.execute(
                    """
                    INSERT INTO trips (source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, revenue, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Dispatched')
                    RETURNING id, source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, revenue, status, created_at
                    """,
                    (source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, revenue)
                )
                trip = cur.fetchone()

                # 4. Atomically update statuses
                cur.execute("UPDATE vehicles SET status = 'On Trip' WHERE id = %s", (vehicle_id,))
                cur.execute("UPDATE drivers SET status = 'On Trip' WHERE id = %s", (driver_id,))

                conn.commit()
                return trip
        except Exception as e:
            conn.rollback()
            raise


# =====================================================================
# CORE TRANSACTION: TRIP COMPLETION
# =====================================================================

def complete_trip(
    trip_id: int,
    final_odometer: float,
    fuel_consumed: float,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    """
    Completes a trip inside an atomic transaction.
    1. Locks and validates trip (must exist and status == 'Dispatched').
    2. Locks and validates vehicle (must exist, final_odometer >= current odometer).
    3. Locks and validates driver.
    4. Updates trip to 'Completed' and records final odometer / fuel consumption.
    5. Resets vehicle status to 'Available' and updates odometer.
    6. Resets driver status to 'Available'.
    """
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                # 1. Lock and check trip status
                cur.execute(
                    "SELECT vehicle_id, driver_id, status FROM trips WHERE id = %s FOR UPDATE",
                    (trip_id,)
                )
                trip = cur.fetchone()
                if not trip:
                    raise EntityNotFoundError(f"Trip {trip_id} not found.")
                if trip["status"] != "Dispatched":
                    raise InvalidStatusTransitionError(f"Trip {trip_id} status is '{trip['status']}', expected 'Dispatched'.")

                vehicle_id = trip["vehicle_id"]
                driver_id = trip["driver_id"]

                # 2. Lock and check vehicle odometer
                cur.execute(
                    "SELECT odometer FROM vehicles WHERE id = %s FOR UPDATE",
                    (vehicle_id,)
                )
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                if final_odometer < float(vehicle["odometer"]):
                    raise InvalidOdometerError(f"Odometer cannot decrease from {vehicle['odometer']} to {final_odometer}.")

                # 3. Lock driver
                cur.execute("SELECT id FROM drivers WHERE id = %s FOR UPDATE", (driver_id,))
                if not cur.fetchone():
                    raise EntityNotFoundError(f"Driver {driver_id} not found.")

                # 4. Update trip details
                cur.execute(
                    """
                    UPDATE trips 
                    SET status = 'Completed', final_odometer = %s, fuel_consumed_liters = %s
                    WHERE id = %s
                    RETURNING id, source, destination, vehicle_id, driver_id, final_odometer, fuel_consumed_liters, status
                    """,
                    (final_odometer, fuel_consumed, trip_id)
                )
                updated_trip = cur.fetchone()

                # 5. Reset vehicle state & update odometer
                cur.execute(
                    "UPDATE vehicles SET odometer = %s, status = 'Available' WHERE id = %s",
                    (final_odometer, vehicle_id)
                )

                # 6. Reset driver state
                cur.execute("UPDATE drivers SET status = 'Available' WHERE id = %s", (driver_id,))

                conn.commit()
                return updated_trip
        except Exception as e:
            conn.rollback()
            raise


# =====================================================================
# CORE TRANSACTION: OPEN MAINTENANCE
# =====================================================================

def open_maintenance(
    vehicle_id: int,
    description: str,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    """
    Puts a vehicle in maintenance inside an atomic transaction.
    1. Locks and validates vehicle (must exist, status != 'Retired').
    2. Switches vehicle status to 'In Shop'.
    3. Creates a new open maintenance log.
    """
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                # 1. Lock and check vehicle
                cur.execute("SELECT status FROM vehicles WHERE id = %s FOR UPDATE", (vehicle_id,))
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                if vehicle["status"] == "Retired":
                    raise ResourceUnavailableError(f"Vehicle {vehicle_id} is retired and cannot be maintained.")

                # 2. Update vehicle status to 'In Shop'
                cur.execute("UPDATE vehicles SET status = 'In Shop' WHERE id = %s", (vehicle_id,))

                # 3. Create open maintenance log
                cur.execute(
                    """
                    INSERT INTO maintenance_logs (vehicle_id, description, cost, status, logged_at)
                    VALUES (%s, %s, 0.00, 'Open', CURRENT_TIMESTAMP)
                    RETURNING id, vehicle_id, description, cost, status, logged_at
                    """,
                    (vehicle_id, description)
                )
                log = cur.fetchone()

                conn.commit()
                return log
        except Exception as e:
            conn.rollback()
            raise


# =====================================================================
# CORE AGGREGATE QUERY: GET FLEET ROI
# =====================================================================

def get_fleet_roi(conn_string: str = CONN_STRING) -> Dict[str, Any]:
    """
    Calculates the aggregate fleet-wide ROI metric using a single raw SQL query:
    ROI = [ (Revenue - (Sum of Maintenance Costs + Sum of Fuel Costs)) / Acquisition Cost ]
    """
    query = """
        SELECT 
            COALESCE(SUM(t.revenue), 0) AS total_revenue,
            COALESCE((SELECT SUM(cost) FROM maintenance_logs), 0) AS total_maintenance_cost,
            COALESCE((SELECT SUM(cost) FROM fuel_logs), 0) AS total_fuel_cost,
            COALESCE((SELECT SUM(acquisition_cost) FROM vehicles), 0) AS total_acquisition_cost,
            CASE 
                WHEN COALESCE((SELECT SUM(acquisition_cost) FROM vehicles), 0) = 0 THEN 0.0
                ELSE ROUND(
                    (
                        COALESCE(SUM(t.revenue), 0) - 
                        (
                            COALESCE((SELECT SUM(cost) FROM maintenance_logs), 0) + 
                            COALESCE((SELECT SUM(cost) FROM fuel_logs), 0)
                        )
                    ) / COALESCE((SELECT SUM(acquisition_cost) FROM vehicles), 0),
                    4
                )
            END AS fleet_roi
        FROM trips t
        WHERE t.status = 'Completed';
    """
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()
            return result if result else {
                "total_revenue": 0.0,
                "total_maintenance_cost": 0.0,
                "total_fuel_cost": 0.0,
                "total_acquisition_cost": 0.0,
                "fleet_roi": 0.0
            }
