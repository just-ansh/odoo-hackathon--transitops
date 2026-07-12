"""
TransitOps Database Utility Module (database.py)
-----------------------------------------------
This module provides high-performance, raw-SQL-based database operations
for the TransitOps platform. It skips ORMs in favor of direct psycopg (Psycopg 3)
interactions and row-level locks for transaction control.

Author: Senior Database Architect & Backend Engineer
"""

import os
import logging
from typing import Dict, Any, List, Optional
import psycopg
from psycopg.rows import dict_row

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Default Connection String (can be overridden via environment variable DATABASE_URL)
DEFAULT_CONN_STRING = "host=localhost dbname=transitops user=postgres password=postgres port=5432"
CONN_STRING = os.getenv("DATABASE_URL", DEFAULT_CONN_STRING)


# =====================================================================
# CUSTOM EXCEPTIONS FOR TRANSACTION SAFETY
# =====================================================================

class TransitOpsDBError(Exception):
    """Base exception class for all TransitOps database errors."""
    pass

class EntityNotFoundError(TransitOpsDBError):
    """Raised when a requested entity (e.g. driver, vehicle, trip) does not exist."""
    pass

class ResourceUnavailableError(TransitOpsDBError):
    """Raised when a resource (e.g. vehicle, driver) is not in 'Available' status."""
    pass

class CapacityExceededError(TransitOpsDBError):
    """Raised when cargo weight exceeds a vehicle's maximum load capacity."""
    pass

class InvalidOdometerError(TransitOpsDBError):
    """Raised when final odometer reading is less than the current odometer reading."""
    pass

class InvalidStatusTransitionError(TransitOpsDBError):
    """Raised when performing operations on a trip that is not in the correct state."""
    pass


# =====================================================================
# CONNECTION HELPER
# =====================================================================

def get_connection(conn_string: str = CONN_STRING) -> psycopg.Connection:
    """
    Establish a connection to the PostgreSQL database.
    Configures dict_row factory globally for all cursors on this connection.
    
    :param conn_string: PostgreSQL connection URI or DSN string.
    :return: An active psycopg Connection object.
    """
    try:
        conn = psycopg.connect(conn_string, row_factory=dict_row)
        return conn
    except psycopg.Error as e:
        logger.error(f"Failed to connect to the database: {e}")
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
    Dispatches a new trip. Ensures that:
    1. Vehicle capacity is sufficient for the cargo weight.
    2. Both driver and vehicle are currently 'Available'.
    3. The trip status is created as 'Dispatched'.
    4. Vehicle and driver statuses are updated atomically to 'On Trip'.
    
    This transaction uses pessimistic locking ('FOR UPDATE') on the vehicle
    and driver records to prevent race conditions (double assignment).
    
    :return: A dictionary containing the details of the created trip.
    """
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                # 1. Row Lock and fetch Vehicle status and capacity
                cur.execute(
                    "SELECT id, max_load_capacity, status FROM vehicles WHERE id = %s FOR UPDATE",
                    (vehicle_id,)
                )
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle with ID {vehicle_id} does not exist.")
                
                # 2. Row Lock and fetch Driver status
                cur.execute(
                    "SELECT id, status FROM drivers WHERE id = %s FOR UPDATE",
                    (driver_id,)
                )
                driver = cur.fetchone()
                if not driver:
                    raise EntityNotFoundError(f"Driver with ID {driver_id} does not exist.")
                
                # 3. Validation: Resource Availability
                if vehicle["status"] != "Available":
                    raise ResourceUnavailableError(
                        f"Vehicle {vehicle_id} cannot be dispatched. Status is '{vehicle['status']}'."
                    )
                if driver["status"] != "Available":
                    raise ResourceUnavailableError(
                        f"Driver {driver_id} cannot be dispatched. Status is '{driver['status']}'."
                    )
                
                # 4. Validation: Capacity check
                # Check capacity using numeric values
                max_cap = float(vehicle["max_load_capacity"])
                if cargo_weight > max_cap:
                    raise CapacityExceededError(
                        f"Cargo weight ({cargo_weight} kg) exceeds vehicle capacity ({max_cap} kg)."
                    )
                
                # 5. Insert Dispatched Trip record
                cur.execute(
                    """
                    INSERT INTO trips (
                        source, destination, vehicle_id, driver_id, cargo_weight, 
                        planned_distance, revenue, status
                    ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Dispatched')
                    RETURNING id, source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, revenue, status, created_at
                    """,
                    (source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, revenue)
                )
                new_trip = cur.fetchone()
                
                # 6. Atomically update Vehicle Status to 'On Trip'
                cur.execute(
                    "UPDATE vehicles SET status = 'On Trip' WHERE id = %s",
                    (vehicle_id,)
                )
                
                # 7. Atomically update Driver Status to 'On Trip'
                cur.execute(
                    "UPDATE drivers SET status = 'On Trip' WHERE id = %s",
                    (driver_id,)
                )
                
                # Commit is handled automatically at the exit of the connection context manager block
                # if no exceptions are raised.
                logger.info(f"Successfully dispatched trip ID {new_trip['id']} using vehicle {vehicle_id} and driver {driver_id}.")
                return new_trip
                
        except Exception as e:
            # Context manager rolls back the transaction upon detecting any raised exception.
            logger.error(f"Dispatch transaction aborted: {e}")
            raise


# =====================================================================
# CORE TRANSACTION: TRIP COMPLETION
# =====================================================================

def complete_trip(
    trip_id: int,
    final_odometer: float,
    fuel_consumed_liters: float,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    """
    Completes a dispatched trip. Safely handles:
    1. Lock and retrieve the Trip record to identify vehicle_id and driver_id.
    2. Lock the associated Vehicle and Driver.
    3. Validate final odometer reading (must be >= current odometer).
    4. Close the trip (status -> 'Completed', sets final odometer and fuel consumed).
    5. Set Vehicle status back to 'Available' and updates its odometer.
    6. Set Driver status back to 'Available'.
    
    :return: A dictionary containing the updated trip record.
    """
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                # 1. Lock and fetch Trip details
                cur.execute(
                    "SELECT id, vehicle_id, driver_id, status FROM trips WHERE id = %s FOR UPDATE",
                    (trip_id,)
                )
                trip = cur.fetchone()
                if not trip:
                    raise EntityNotFoundError(f"Trip with ID {trip_id} does not exist.")
                
                # Validate Trip state
                if trip["status"] != "Dispatched":
                    raise InvalidStatusTransitionError(
                        f"Cannot complete trip {trip_id}. Trip status is '{trip['status']}', expected 'Dispatched'."
                    )
                
                vehicle_id = trip["vehicle_id"]
                driver_id = trip["driver_id"]
                
                # 2. Lock Vehicle and Driver rows
                cur.execute(
                    "SELECT id, odometer, status FROM vehicles WHERE id = %s FOR UPDATE",
                    (vehicle_id,)
                )
                vehicle = cur.fetchone()
                
                cur.execute(
                    "SELECT id, status FROM drivers WHERE id = %s FOR UPDATE",
                    (driver_id,)
                )
                driver = cur.fetchone()
                
                # 3. Validate Odometer reading
                current_odo = float(vehicle["odometer"])
                if final_odometer < current_odo:
                    raise InvalidOdometerError(
                        f"Final odometer reading ({final_odometer}) cannot be less than current odometer ({current_odo})."
                    )
                
                # 4. Update the Trip status to 'Completed'
                cur.execute(
                    """
                    UPDATE trips 
                    SET status = 'Completed', 
                        final_odometer = %s, 
                        fuel_consumed_liters = %s
                    WHERE id = %s
                    RETURNING id, source, destination, vehicle_id, driver_id, cargo_weight, 
                              planned_distance, final_odometer, fuel_consumed_liters, revenue, status, created_at
                    """,
                    (final_odometer, fuel_consumed_liters, trip_id)
                )
                updated_trip = cur.fetchone()
                
                # 5. Update Vehicle: Update odometer and set status back to 'Available'
                cur.execute(
                    """
                    UPDATE vehicles 
                    SET odometer = %s, 
                        status = 'Available' 
                    WHERE id = %s
                    """,
                    (final_odometer, vehicle_id)
                )
                
                # 6. Update Driver: Set status back to 'Available'
                cur.execute(
                    "UPDATE drivers SET status = 'Available' WHERE id = %s",
                    (driver_id,)
                )
                
                logger.info(f"Successfully completed trip ID {trip_id}. Vehicle odometer updated to {final_odometer}.")
                return updated_trip
                
        except Exception as e:
            logger.error(f"Complete trip transaction aborted: {e}")
            raise


# =====================================================================
# AGGREGATE QUERY: VEHICLE ROI CALCULATION
# =====================================================================

def calculate_vehicle_roi(conn_string: str = CONN_STRING) -> List[Dict[str, Any]]:
    """
    Calculates return-on-investment (ROI) for all vehicles using the formula:
    ROI = [ (Revenue - (Sum of Maintenance Costs + Sum of Fuel Costs)) / Acquisition Cost ]
    
    This is executed as a high-performance single query, utilizing pre-aggregated subqueries
    to ensure accuracy and prevent cross-join duplication.
    
    :return: A list of dictionaries representing ROI details for each vehicle.
    """
    query = """
        SELECT 
            v.id AS vehicle_id,
            v.registration_number,
            v.name_model,
            v.acquisition_cost,
            COALESCE(r.total_revenue, 0) AS total_revenue,
            COALESCE(m.total_maintenance, 0) AS total_maintenance,
            COALESCE(f.total_fuel, 0) AS total_fuel,
            CASE 
                WHEN v.acquisition_cost = 0 THEN 0.0
                ELSE ROUND(
                    (COALESCE(r.total_revenue, 0) - (COALESCE(m.total_maintenance, 0) + COALESCE(f.total_fuel, 0))) 
                    / v.acquisition_cost, 4
                )
            END AS roi
        FROM vehicles v
        LEFT JOIN (
            SELECT vehicle_id, SUM(revenue) AS total_revenue
            FROM trips
            WHERE status = 'Completed'
            GROUP BY vehicle_id
        ) r ON r.vehicle_id = v.id
        LEFT JOIN (
            SELECT vehicle_id, SUM(cost) AS total_maintenance
            FROM maintenance_logs
            GROUP BY vehicle_id
        ) m ON m.vehicle_id = v.id
        LEFT JOIN (
            SELECT vehicle_id, SUM(cost) AS total_fuel
            FROM fuel_logs
            GROUP BY vehicle_id
        ) f ON f.vehicle_id = v.id
        ORDER BY roi DESC, v.id ASC;
    """
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
