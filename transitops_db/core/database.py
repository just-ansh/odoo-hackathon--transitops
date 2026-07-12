"""
TransitOps Database Utility Module (core/database.py)
-----------------------------------------------------
Handles raw SQL database connections, row-to-dictionary factory configuration,
and atomic business logic transactions using row-level locking.

Author: Developer 1 (Senior Database Architect & Backend Engineer)
"""

import os
import logging
from typing import Dict, Any, List, Optional
import psycopg
from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation

logger = logging.getLogger(__name__)

DEFAULT_CONN_STRING = "host=192.168.0.9 dbname=transitops user=postgres password=1234 port=5432"
CONN_STRING = os.getenv("DATABASE_URL", DEFAULT_CONN_STRING)


# =====================================================================
# CUSTOM EXCEPTIONS
# =====================================================================

class TransitOpsDBError(Exception):
    pass

class EntityNotFoundError(TransitOpsDBError):
    pass

class ResourceUnavailableError(TransitOpsDBError):
    pass

class CapacityExceededError(TransitOpsDBError):
    pass

class InvalidOdometerError(TransitOpsDBError):
    pass

class InvalidStatusTransitionError(TransitOpsDBError):
    pass

class DuplicateEntryError(TransitOpsDBError):
    """Raised when a unique constraint is violated (e.g. duplicate registration number)."""
    pass


# =====================================================================
# CONNECTION HELPER
# =====================================================================

def get_connection(conn_string: str = CONN_STRING) -> psycopg.Connection:
    try:
        return psycopg.connect(conn_string, row_factory=dict_row)
    except psycopg.Error as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise TransitOpsDBError(f"Database connection failed: {e}")


# =====================================================================
# LIST QUERIES — VEHICLES
# =====================================================================

def get_vehicles(
    status: Optional[str] = None,
    type: Optional[str] = None,
    conn_string: str = CONN_STRING
) -> List[Dict[str, Any]]:
    """Returns all vehicles, with optional filtering by status and/or type."""
    filters = []
    params = []
    if status:
        filters.append("status = %s")
        params.append(status)
    if type:
        filters.append("type = %s")
        params.append(type)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT id, registration_number, name_model, type, max_load_capacity,
               odometer, acquisition_cost, status, region, created_at
        FROM vehicles
        {where}
        ORDER BY id ASC
    """
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


# =====================================================================
# LIST QUERIES — DRIVERS
# =====================================================================

def get_drivers(
    status: Optional[str] = None,
    conn_string: str = CONN_STRING
) -> List[Dict[str, Any]]:
    """Returns all drivers, with optional filtering by status."""
    filters = []
    params = []
    if status:
        filters.append("status = %s")
        params.append(status)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT id, name, license_number, license_category, license_expiry_date,
               contact_number, safety_score, status, created_at
        FROM drivers
        {where}
        ORDER BY id ASC
    """
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


# =====================================================================
# LIST QUERIES — TRIPS
# =====================================================================

def get_trips(
    status: Optional[str] = None,
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    conn_string: str = CONN_STRING
) -> List[Dict[str, Any]]:
    """Returns all trips, with optional filtering by status, vehicle_id, driver_id."""
    filters = []
    params = []
    if status:
        filters.append("status = %s")
        params.append(status)
    if vehicle_id:
        filters.append("vehicle_id = %s")
        params.append(vehicle_id)
    if driver_id:
        filters.append("driver_id = %s")
        params.append(driver_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT id, source, destination, vehicle_id, driver_id, cargo_weight,
               planned_distance, final_odometer, fuel_consumed_liters, revenue, status, created_at
        FROM trips
        {where}
        ORDER BY created_at DESC
    """
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


# =====================================================================
# LIST QUERIES — MAINTENANCE LOGS
# =====================================================================

def get_maintenance_logs(
    vehicle_id: Optional[int] = None,
    status: Optional[str] = None,
    conn_string: str = CONN_STRING
) -> List[Dict[str, Any]]:
    """Returns all maintenance logs, with optional filtering by vehicle_id and/or status."""
    filters = []
    params = []
    if vehicle_id:
        filters.append("vehicle_id = %s")
        params.append(vehicle_id)
    if status:
        filters.append("status = %s")
        params.append(status)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT id, vehicle_id, description, cost, status, logged_at, closed_at
        FROM maintenance_logs
        {where}
        ORDER BY logged_at DESC
    """
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


# =====================================================================
# LIST QUERIES — FUEL LOGS
# =====================================================================

def get_fuel_logs(
    vehicle_id: Optional[int] = None,
    trip_id: Optional[int] = None,
    conn_string: str = CONN_STRING
) -> List[Dict[str, Any]]:
    """Returns all fuel logs, with optional filtering by vehicle_id and/or trip_id."""
    filters = []
    params = []
    if vehicle_id:
        filters.append("vehicle_id = %s")
        params.append(vehicle_id)
    if trip_id:
        filters.append("trip_id = %s")
        params.append(trip_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT id, vehicle_id, trip_id, liters, cost, logged_date
        FROM fuel_logs
        {where}
        ORDER BY logged_date DESC
    """
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


# =====================================================================
# LIST QUERIES — EXPENSES
# =====================================================================

def get_expenses(
    vehicle_id: Optional[int] = None,
    type: Optional[str] = None,
    conn_string: str = CONN_STRING
) -> List[Dict[str, Any]]:
    """Returns all expenses, with optional filtering by vehicle_id and/or type."""
    filters = []
    params = []
    if vehicle_id:
        filters.append("vehicle_id = %s")
        params.append(vehicle_id)
    if type:
        filters.append("type = %s")
        params.append(type)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT id, vehicle_id, type, amount, description, logged_date
        FROM expenses
        {where}
        ORDER BY logged_date DESC
    """
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


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
    Dispatches a trip atomically:
    - Locks vehicle: validates 'Available' status and cargo capacity.
    - Locks driver: validates 'Available' status.
    - Inserts trip as 'Dispatched'.
    - Sets both vehicle and driver to 'On Trip'.
    """
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT max_load_capacity, status FROM vehicles WHERE id = %s FOR UPDATE",
                    (vehicle_id,)
                )
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                if vehicle["status"] != "Available":
                    raise ResourceUnavailableError(
                        f"Vehicle {vehicle_id} is '{vehicle['status']}', expected 'Available'."
                    )
                if cargo_weight > float(vehicle["max_load_capacity"]):
                    raise CapacityExceededError(
                        f"Cargo weight {cargo_weight}kg exceeds vehicle capacity {vehicle['max_load_capacity']}kg."
                    )

                cur.execute(
                    "SELECT status FROM drivers WHERE id = %s FOR UPDATE",
                    (driver_id,)
                )
                driver = cur.fetchone()
                if not driver:
                    raise EntityNotFoundError(f"Driver {driver_id} not found.")
                if driver["status"] != "Available":
                    raise ResourceUnavailableError(
                        f"Driver {driver_id} is '{driver['status']}', expected 'Available'."
                    )

                cur.execute(
                    """
                    INSERT INTO trips
                        (source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, revenue, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Dispatched')
                    RETURNING id, source, destination, vehicle_id, driver_id, cargo_weight,
                              planned_distance, revenue, status, created_at
                    """,
                    (source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, revenue)
                )
                trip = cur.fetchone()

                cur.execute("UPDATE vehicles SET status = 'On Trip' WHERE id = %s", (vehicle_id,))
                cur.execute("UPDATE drivers SET status = 'On Trip' WHERE id = %s", (driver_id,))
                conn.commit()
                return trip
        except Exception:
            conn.rollback()
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
    Completes a dispatched trip atomically:
    - Validates trip is 'Dispatched'.
    - Validates final odometer >= current odometer.
    - Updates trip to 'Completed', records final_odometer and fuel_consumed_liters.
    - Restores vehicle odometer and status to 'Available'.
    - Restores driver status to 'Available'.
    """
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT vehicle_id, driver_id, status FROM trips WHERE id = %s FOR UPDATE",
                    (trip_id,)
                )
                trip = cur.fetchone()
                if not trip:
                    raise EntityNotFoundError(f"Trip {trip_id} not found.")
                if trip["status"] != "Dispatched":
                    raise InvalidStatusTransitionError(
                        f"Trip {trip_id} status is '{trip['status']}', expected 'Dispatched'."
                    )

                vehicle_id = trip["vehicle_id"]
                driver_id = trip["driver_id"]

                cur.execute(
                    "SELECT odometer FROM vehicles WHERE id = %s FOR UPDATE",
                    (vehicle_id,)
                )
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                if final_odometer < float(vehicle["odometer"]):
                    raise InvalidOdometerError(
                        f"Final odometer ({final_odometer}) cannot be less than current odometer ({vehicle['odometer']})."
                    )

                cur.execute("SELECT id FROM drivers WHERE id = %s FOR UPDATE", (driver_id,))
                if not cur.fetchone():
                    raise EntityNotFoundError(f"Driver {driver_id} not found.")

                cur.execute(
                    """
                    UPDATE trips
                    SET status = 'Completed',
                        final_odometer = %s,
                        fuel_consumed_liters = %s
                    WHERE id = %s
                    RETURNING id, source, destination, vehicle_id, driver_id,
                              final_odometer, fuel_consumed_liters, revenue, status, created_at
                    """,
                    (final_odometer, fuel_consumed_liters, trip_id)
                )
                updated_trip = cur.fetchone()

                cur.execute(
                    "UPDATE vehicles SET odometer = %s, status = 'Available' WHERE id = %s",
                    (final_odometer, vehicle_id)
                )
                cur.execute("UPDATE drivers SET status = 'Available' WHERE id = %s", (driver_id,))
                conn.commit()
                return updated_trip
        except Exception:
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
    Opens a maintenance log atomically and sets vehicle status to 'In Shop'.
    Vehicle must not be 'Retired'.
    """
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT status FROM vehicles WHERE id = %s FOR UPDATE",
                    (vehicle_id,)
                )
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                if vehicle["status"] == "Retired":
                    raise ResourceUnavailableError(
                        f"Vehicle {vehicle_id} is 'Retired' and cannot receive maintenance."
                    )

                cur.execute("UPDATE vehicles SET status = 'In Shop' WHERE id = %s", (vehicle_id,))
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
        except Exception:
            conn.rollback()
            raise


# =====================================================================
# CORE TRANSACTION: CLOSE MAINTENANCE
# =====================================================================

def close_maintenance(
    log_id: int,
    cost: float,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    """
    Closes an open maintenance log atomically:
    - Validates the log exists and is 'Open'.
    - Updates the log to 'Closed' with the final cost and closed_at timestamp.
    - Restores vehicle status to 'Available'.
    """
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT vehicle_id, status FROM maintenance_logs WHERE id = %s FOR UPDATE",
                    (log_id,)
                )
                log = cur.fetchone()
                if not log:
                    raise EntityNotFoundError(f"Maintenance log {log_id} not found.")
                if log["status"] != "Open":
                    raise InvalidStatusTransitionError(
                        f"Maintenance log {log_id} is already '{log['status']}', expected 'Open'."
                    )

                vehicle_id = log["vehicle_id"]

                cur.execute(
                    """
                    UPDATE maintenance_logs
                    SET status = 'Closed', cost = %s, closed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, vehicle_id, description, cost, status, logged_at, closed_at
                    """,
                    (cost, log_id)
                )
                updated_log = cur.fetchone()

                cur.execute(
                    "UPDATE vehicles SET status = 'Available' WHERE id = %s",
                    (vehicle_id,)
                )
                conn.commit()
                return updated_log
        except Exception:
            conn.rollback()
            raise


# =====================================================================
# WRITE: ADD FUEL LOG
# =====================================================================

def add_fuel_log(
    vehicle_id: int,
    liters: float,
    cost: float,
    logged_date: str,
    trip_id: Optional[int] = None,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    """Inserts a new fuel log entry for a vehicle, optionally tied to a specific trip."""
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM vehicles WHERE id = %s", (vehicle_id,))
                if not cur.fetchone():
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")

                if trip_id:
                    cur.execute("SELECT id FROM trips WHERE id = %s", (trip_id,))
                    if not cur.fetchone():
                        raise EntityNotFoundError(f"Trip {trip_id} not found.")

                cur.execute(
                    """
                    INSERT INTO fuel_logs (vehicle_id, trip_id, liters, cost, logged_date)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, vehicle_id, trip_id, liters, cost, logged_date
                    """,
                    (vehicle_id, trip_id, liters, cost, logged_date)
                )
                log = cur.fetchone()
                conn.commit()
                return log
        except Exception:
            conn.rollback()
            raise


# =====================================================================
# WRITE: ADD EXPENSE
# =====================================================================

def add_expense(
    vehicle_id: int,
    type: str,
    amount: float,
    description: str,
    logged_date: str,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    """Inserts a new expense entry (Tolls, Maintenance, Other) for a vehicle."""
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM vehicles WHERE id = %s", (vehicle_id,))
                if not cur.fetchone():
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")

                cur.execute(
                    """
                    INSERT INTO expenses (vehicle_id, type, amount, description, logged_date)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, vehicle_id, type, amount, description, logged_date
                    """,
                    (vehicle_id, type, amount, description, logged_date)
                )
                expense = cur.fetchone()
                conn.commit()
                return expense
        except Exception:
            conn.rollback()
            raise


# =====================================================================
# AGGREGATE QUERY: FLEET-WIDE ROI
# =====================================================================

def get_fleet_roi(conn_string: str = CONN_STRING) -> Dict[str, Any]:
    """
    Returns a single aggregate row of fleet-wide ROI metrics.
    ROI = (Revenue - (Maintenance Costs + Fuel Costs + Other Expenses)) / Total Acquisition Cost
    """
    query = """
        SELECT
            COALESCE(SUM(t.revenue), 0)                                   AS total_revenue,
            COALESCE((SELECT SUM(cost) FROM maintenance_logs), 0) +
            COALESCE((SELECT SUM(amount) FROM expenses WHERE type = 'Maintenance'), 0) AS total_maintenance_cost,
            COALESCE((SELECT SUM(cost) FROM fuel_logs), 0)                AS total_fuel_cost,
            COALESCE((SELECT SUM(amount) FROM expenses WHERE type != 'Maintenance'), 0) AS total_other_expense_cost,
            COALESCE((SELECT SUM(acquisition_cost) FROM vehicles), 0)     AS total_acquisition_cost,
            CASE
                WHEN COALESCE((SELECT SUM(acquisition_cost) FROM vehicles), 0) = 0 THEN 0.0
                ELSE ROUND(
                    (
                        COALESCE(SUM(t.revenue), 0) -
                        (
                            COALESCE((SELECT SUM(cost) FROM maintenance_logs), 0) +
                            COALESCE((SELECT SUM(amount) FROM expenses WHERE type = 'Maintenance'), 0) +
                            COALESCE((SELECT SUM(cost) FROM fuel_logs), 0) +
                            COALESCE((SELECT SUM(amount) FROM expenses WHERE type != 'Maintenance'), 0)
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
            return result or {
                "total_revenue": 0.0,
                "total_maintenance_cost": 0.0,
                "total_fuel_cost": 0.0,
                "total_other_expense_cost": 0.0,
                "total_acquisition_cost": 0.0,
                "fleet_roi": 0.0
            }


# =====================================================================
# AGGREGATE QUERY: PER-VEHICLE ROI BREAKDOWN
# =====================================================================

def get_vehicle_roi_breakdown(conn_string: str = CONN_STRING) -> List[Dict[str, Any]]:
    """
    Returns ROI metrics broken down per vehicle using pre-aggregated subqueries
    to avoid cross-join row multiplication.
    ROI = (Revenue - (Maintenance Costs + Fuel Costs + Other Expenses)) / Acquisition Cost
    """
    query = """
        SELECT
            v.id                                        AS vehicle_id,
            v.registration_number,
            v.name_model,
            v.type,
            v.acquisition_cost,
            COALESCE(r.total_revenue, 0)                AS total_revenue,
            (COALESCE(m.total_maintenance, 0) + COALESCE(e.maintenance_expenses, 0)) AS total_maintenance,
            COALESCE(f.total_fuel, 0)                   AS total_fuel,
            COALESCE(e.other_expenses, 0)               AS total_other_expense,
            CASE
                WHEN v.acquisition_cost = 0 THEN 0.0
                ELSE ROUND(
                    (
                        COALESCE(r.total_revenue, 0) -
                        (
                            COALESCE(m.total_maintenance, 0) + 
                            COALESCE(e.maintenance_expenses, 0) + 
                            COALESCE(f.total_fuel, 0) + 
                            COALESCE(e.other_expenses, 0)
                        )
                    ) / v.acquisition_cost,
                    4
                )
            END AS roi
        FROM vehicles v
        LEFT JOIN (
            SELECT vehicle_id, SUM(revenue) AS total_revenue
            FROM trips WHERE status = 'Completed'
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
        LEFT JOIN (
            SELECT vehicle_id,
                   SUM(CASE WHEN type = 'Maintenance' THEN amount ELSE 0 END) AS maintenance_expenses,
                   SUM(CASE WHEN type != 'Maintenance' THEN amount ELSE 0 END) AS other_expenses
            FROM expenses
            GROUP BY vehicle_id
        ) e ON e.vehicle_id = v.id
        ORDER BY roi DESC NULLS LAST, v.id ASC;
    """
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


# =====================================================================
# VEHICLES CRUD METHODS
# =====================================================================

def create_vehicle(
    registration_number: str,
    name_model: str,
    type: str,
    max_load_capacity: float,
    odometer: float,
    acquisition_cost: float,
    status: str = "Available",
    region: Optional[str] = None,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                # Check uniqueness
                cur.execute("SELECT id FROM vehicles WHERE registration_number = %s", (registration_number,))
                if cur.fetchone():
                    raise DuplicateEntryError(f"Vehicle with registration number {registration_number} already exists.")
                
                cur.execute(
                    """
                    INSERT INTO vehicles 
                        (registration_number, name_model, type, max_load_capacity, odometer, acquisition_cost, status, region)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, registration_number, name_model, type, max_load_capacity, odometer, acquisition_cost, status, region, created_at
                    """,
                    (registration_number, name_model, type, max_load_capacity, odometer, acquisition_cost, status, region)
                )
                vehicle = cur.fetchone()
                conn.commit()
                return vehicle
        except UniqueViolation:
            conn.rollback()
            raise DuplicateEntryError(f"Vehicle with registration number {registration_number} already exists.")
        except Exception:
            conn.rollback()
            raise

def update_vehicle(
    vehicle_id: int,
    updates: Dict[str, Any],
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    if not updates:
        return get_vehicle_by_id(vehicle_id, conn_string)
        
    fields = []
    params = []
    for k, v in updates.items():
        fields.append(f"{k} = %s")
        params.append(v)
    params.append(vehicle_id)
    
    query = f"""
        UPDATE vehicles
        SET {', '.join(fields)}
        WHERE id = %s
        RETURNING id, registration_number, name_model, type, max_load_capacity, odometer, acquisition_cost, status, region, created_at
    """
    
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                conn.commit()
                return vehicle
        except UniqueViolation:
            conn.rollback()
            raise DuplicateEntryError("A vehicle with this registration number already exists.")
        except Exception:
            conn.rollback()
            raise

def delete_vehicle(
    vehicle_id: int,
    conn_string: str = CONN_STRING
) -> None:
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT status FROM vehicles WHERE id = %s", (vehicle_id,))
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                cur.execute("DELETE FROM vehicles WHERE id = %s", (vehicle_id,))
                conn.commit()
        except Exception:
            conn.rollback()
            raise

def get_vehicle_by_id(
    vehicle_id: int,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, registration_number, name_model, type, max_load_capacity, odometer, acquisition_cost, status, region, created_at
                FROM vehicles WHERE id = %s
                """,
                (vehicle_id,)
            )
            vehicle = cur.fetchone()
            if not vehicle:
                raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
            return vehicle


# =====================================================================
# DRIVERS CRUD METHODS
# =====================================================================

def create_driver(
    name: str,
    license_number: str,
    license_category: str,
    license_expiry_date: str,
    contact_number: str,
    safety_score: float = 100.0,
    status: str = "Available",
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM drivers WHERE license_number = %s", (license_number,))
                if cur.fetchone():
                    raise DuplicateEntryError(f"Driver with license number {license_number} already exists.")
                
                cur.execute(
                    """
                    INSERT INTO drivers 
                        (name, license_number, license_category, license_expiry_date, contact_number, safety_score, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, name, license_number, license_category, license_expiry_date, contact_number, safety_score, status, created_at
                    """,
                    (name, license_number, license_category, license_expiry_date, contact_number, safety_score, status)
                )
                driver = cur.fetchone()
                conn.commit()
                return driver
        except UniqueViolation:
            conn.rollback()
            raise DuplicateEntryError(f"Driver with license number {license_number} already exists.")
        except Exception:
            conn.rollback()
            raise

def update_driver(
    driver_id: int,
    updates: Dict[str, Any],
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    if not updates:
        return get_driver_by_id(driver_id, conn_string)
        
    fields = []
    params = []
    for k, v in updates.items():
        fields.append(f"{k} = %s")
        params.append(v)
    params.append(driver_id)
    
    query = f"""
        UPDATE drivers
        SET {', '.join(fields)}
        WHERE id = %s
        RETURNING id, name, license_number, license_category, license_expiry_date, contact_number, safety_score, status, created_at
    """
    
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                driver = cur.fetchone()
                if not driver:
                    raise EntityNotFoundError(f"Driver {driver_id} not found.")
                conn.commit()
                return driver
        except UniqueViolation:
            conn.rollback()
            raise DuplicateEntryError("A driver with this license number already exists.")
        except Exception:
            conn.rollback()
            raise

def delete_driver(
    driver_id: int,
    conn_string: str = CONN_STRING
) -> None:
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT status FROM drivers WHERE id = %s", (driver_id,))
                driver = cur.fetchone()
                if not driver:
                    raise EntityNotFoundError(f"Driver {driver_id} not found.")
                cur.execute("DELETE FROM drivers WHERE id = %s", (driver_id,))
                conn.commit()
        except Exception:
            conn.rollback()
            raise

def get_driver_by_id(
    driver_id: int,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, license_number, license_category, license_expiry_date, contact_number, safety_score, status, created_at
                FROM drivers WHERE id = %s
                """,
                (driver_id,)
            )
            driver = cur.fetchone()
            if not driver:
                raise EntityNotFoundError(f"Driver {driver_id} not found.")
            return driver


# =====================================================================
# TRIPS CREATION & LIFECYCLE
# =====================================================================

def create_trip(
    source: str,
    destination: str,
    vehicle_id: int,
    driver_id: int,
    cargo_weight: float,
    planned_distance: float,
    revenue: float = 0.0,
    status: str = "Draft",
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    if status == "Dispatched":
        return dispatch_trip(
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            cargo_weight=cargo_weight,
            source=source,
            destination=destination,
            planned_distance=planned_distance,
            revenue=revenue,
            conn_string=conn_string
        )
        
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM vehicles WHERE id = %s", (vehicle_id,))
                if not cur.fetchone():
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                cur.execute("SELECT id FROM drivers WHERE id = %s", (driver_id,))
                if not cur.fetchone():
                    raise EntityNotFoundError(f"Driver {driver_id} not found.")
                
                cur.execute(
                    """
                    INSERT INTO trips
                        (source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, revenue, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, source, destination, vehicle_id, driver_id, cargo_weight,
                              planned_distance, final_odometer, fuel_consumed_liters, revenue, status, created_at
                    """,
                    (source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, revenue, status)
                )
                trip = cur.fetchone()
                conn.commit()
                return trip
        except Exception:
            conn.rollback()
            raise

def dispatch_trip_by_id(
    trip_id: int,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT vehicle_id, driver_id, cargo_weight, status FROM trips WHERE id = %s FOR UPDATE",
                    (trip_id,)
                )
                trip = cur.fetchone()
                if not trip:
                    raise EntityNotFoundError(f"Trip {trip_id} not found.")
                if trip["status"] != "Draft":
                    raise InvalidStatusTransitionError(
                        f"Trip {trip_id} status is '{trip['status']}', expected 'Draft' for dispatching."
                    )
                
                vehicle_id = trip["vehicle_id"]
                driver_id = trip["driver_id"]
                cargo_weight = float(trip["cargo_weight"])
                
                cur.execute(
                    "SELECT max_load_capacity, status FROM vehicles WHERE id = %s FOR UPDATE",
                    (vehicle_id,)
                )
                vehicle = cur.fetchone()
                if not vehicle:
                    raise EntityNotFoundError(f"Vehicle {vehicle_id} not found.")
                if vehicle["status"] != "Available":
                    raise ResourceUnavailableError(
                        f"Vehicle {vehicle_id} is '{vehicle['status']}', expected 'Available'."
                    )
                if cargo_weight > float(vehicle["max_load_capacity"]):
                    raise CapacityExceededError(
                        f"Cargo weight {cargo_weight}kg exceeds vehicle capacity {vehicle['max_load_capacity']}kg."
                    )

                cur.execute(
                    "SELECT status FROM drivers WHERE id = %s FOR UPDATE",
                    (driver_id,)
                )
                driver = cur.fetchone()
                if not driver:
                    raise EntityNotFoundError(f"Driver {driver_id} not found.")
                if driver["status"] != "Available":
                    raise ResourceUnavailableError(
                        f"Driver {driver_id} is '{driver['status']}', expected 'Available'."
                    )

                cur.execute(
                    """
                    UPDATE trips
                    SET status = 'Dispatched'
                    WHERE id = %s
                    RETURNING id, source, destination, vehicle_id, driver_id, cargo_weight,
                              planned_distance, final_odometer, fuel_consumed_liters, revenue, status, created_at
                    """,
                    (trip_id,)
                )
                updated_trip = cur.fetchone()

                cur.execute("UPDATE vehicles SET status = 'On Trip' WHERE id = %s", (vehicle_id,))
                cur.execute("UPDATE drivers SET status = 'On Trip' WHERE id = %s", (driver_id,))
                conn.commit()
                return updated_trip
        except Exception:
            conn.rollback()
            raise

def cancel_trip(
    trip_id: int,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    with get_connection(conn_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT vehicle_id, driver_id, status FROM trips WHERE id = %s FOR UPDATE",
                    (trip_id,)
                )
                trip = cur.fetchone()
                if not trip:
                    raise EntityNotFoundError(f"Trip {trip_id} not found.")
                
                if trip["status"] in ("Completed", "Cancelled"):
                    raise InvalidStatusTransitionError(
                        f"Cannot cancel trip {trip_id} with current status '{trip['status']}'."
                    )
                
                old_status = trip["status"]
                
                cur.execute(
                    """
                    UPDATE trips
                    SET status = 'Cancelled'
                    WHERE id = %s
                    RETURNING id, source, destination, vehicle_id, driver_id, cargo_weight,
                              planned_distance, final_odometer, fuel_consumed_liters, revenue, status, created_at
                    """,
                    (trip_id,)
                )
                updated_trip = cur.fetchone()
                
                if old_status == "Dispatched":
                    vehicle_id = trip["vehicle_id"]
                    driver_id = trip["driver_id"]
                    cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = %s", (vehicle_id,))
                    cur.execute("UPDATE drivers SET status = 'Available' WHERE id = %s", (driver_id,))
                    
                conn.commit()
                return updated_trip
        except Exception:
            conn.rollback()
            raise


# =====================================================================
# DASHBOARD / STATISTICS
# =====================================================================

def get_dashboard_kpis(
    vehicle_type: Optional[str] = None,
    status: Optional[str] = None,
    region: Optional[str] = None,
    conn_string: str = CONN_STRING
) -> Dict[str, Any]:
    filters = []
    params = []
    if vehicle_type:
        filters.append("type = %s")
        params.append(vehicle_type)
    if status:
        filters.append("status = %s")
        params.append(status)
    if region:
        filters.append("region = %s")
        params.append(region)
        
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    
    with get_connection(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) as total, SUM(CASE WHEN status = 'On Trip' THEN 1 ELSE 0 END) as active, SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available, SUM(CASE WHEN status = 'In Shop' THEN 1 ELSE 0 END) as shop FROM vehicles {where_clause}", params)
            v_stats = cur.fetchone()
            total_vehicles = v_stats["total"] or 0
            active_vehicles = v_stats["active"] or 0
            available_vehicles = v_stats["available"] or 0
            in_maintenance = v_stats["shop"] or 0
            
            if where_clause:
                trip_query_active = f"SELECT COUNT(*) FROM trips WHERE status = 'Dispatched' AND vehicle_id IN (SELECT id FROM vehicles {where_clause})"
                trip_query_pending = f"SELECT COUNT(*) FROM trips WHERE status = 'Draft' AND vehicle_id IN (SELECT id FROM vehicles {where_clause})"
                cur.execute(trip_query_active, params)
                active_trips = cur.fetchone()["count"] or 0
                cur.execute(trip_query_pending, params)
                pending_trips = cur.fetchone()["count"] or 0
            else:
                cur.execute("SELECT COUNT(*) FROM trips WHERE status = 'Dispatched'")
                active_trips = cur.fetchone()["count"] or 0
                cur.execute("SELECT COUNT(*) FROM trips WHERE status = 'Draft'")
                pending_trips = cur.fetchone()["count"] or 0
                
            cur.execute("SELECT COUNT(*) FROM drivers WHERE status IN ('Available', 'On Trip')")
            drivers_on_duty = cur.fetchone()["count"] or 0
            
            utilization = round((float(active_vehicles) / float(total_vehicles) * 100), 2) if total_vehicles > 0 else 0.0
            
            return {
                "active_vehicles": active_vehicles,
                "available_vehicles": available_vehicles,
                "vehicles_in_maintenance": in_maintenance,
                "active_trips": active_trips,
                "pending_trips": pending_trips,
                "drivers_on_duty": drivers_on_duty,
                "fleet_utilization_pct": utilization
            }


# =====================================================================
# ALIASES FOR COMPATIBILITY
# =====================================================================
calculate_vehicle_roi = get_vehicle_roi_breakdown

