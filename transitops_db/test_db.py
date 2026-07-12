"""
TransitOps Database Verification Script (test_db.py)
---------------------------------------------------
This script automates:
1. Re-creating the 'transitops' database on local PostgreSQL.
2. Executing 'schema.sql' DDL.
3. Seeding mock data using 'seed.sql'.
4. Executing unit-test scenarios for transactions (Dispatch, Completion, and ROI).

Run this with python: `python test_db.py`
"""

import os
import sys
import psycopg
from psycopg.rows import dict_row
from core.database import (
    CONN_STRING,
    get_connection,
    dispatch_trip,
    complete_trip,
    calculate_vehicle_roi,
    EntityNotFoundError,
    ResourceUnavailableError,
    CapacityExceededError,
    InvalidOdometerError,
    InvalidStatusTransitionError
)

def run_sql_file(conn, file_path: str):
    """Utility to execute all SQL commands from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Enable autocommit for creating/dropping databases, but here we run in transaction
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"Executed SQL script: {file_path}")

def reset_database():
    """Connect to default 'postgres' database to recreate 'transitops' database."""
    print("Re-creating 'transitops' database...")
    # Parse default connection string to connect to 'postgres' DB first
    # to perform drop/create database.
    admin_conn_string = CONN_STRING.replace("dbname=transitops", "dbname=postgres")
    
    try:
        # Connect to admin db
        conn = psycopg.connect(admin_conn_string, autocommit=True)
        with conn.cursor() as cur:
            # Check if transitops DB exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'transitops'")
            exists = cur.fetchone()
            if exists:
                # Terminate other sessions to allow drop
                cur.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = 'transitops'
                      AND pid <> pg_backend_pid();
                """)
                cur.execute("DROP DATABASE transitops")
                print("Dropped existing 'transitops' database.")
            
            cur.execute("CREATE DATABASE transitops")
            print("Created new 'transitops' database.")
        conn.close()
    except Exception as e:
        print(f"Warning: Could not recreate database automatically: {e}")
        print("Continuing by running schema.sql directly on current target database...")

def main():
    # Get base directory of this script to locate schema and seed sql files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(base_dir, "sql", "schema.sql")
    seed_file = os.path.join(base_dir, "sql", "seed.sql")

    # 1. Reset and Rebuild Database
    reset_database()
    
    # 2. Establish connection to transitops and run schema/seed
    try:
        conn = get_connection(CONN_STRING)
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print(f"Please ensure PostgreSQL is running and you can connect with: '{CONN_STRING}'")
        sys.exit(1)
        
    try:
        print("\n--- Initializing Schema and Seeding Data ---")
        run_sql_file(conn, schema_file)
        run_sql_file(conn, seed_file)
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to run schema/seed: {e}")
        sys.exit(1)

    print("\n--- Starting Transaction Unit Tests ---")
    
    # Test Case 1: Successful Trip Dispatch
    print("\nTest Case 1: Dispatching Trip (Vehicle ID 5, Driver ID 5)...")
    try:
        trip = dispatch_trip(
            vehicle_id=5,
            driver_id=5,
            cargo_weight=15000.00,
            source="Austin, TX",
            destination="Dallas, TX",
            planned_distance=200.00,
            revenue=1400.00
        )
        print(f"SUCCESS: Trip dispatched successfully! Trip ID: {trip['id']}, Status: {trip['status']}")
        
        # Verify status in database
        with get_connection() as c:
            with c.cursor() as cur:
                cur.execute("SELECT status FROM vehicles WHERE id = 5")
                v_status = cur.fetchone()["status"]
                cur.execute("SELECT status FROM drivers WHERE id = 5")
                d_status = cur.fetchone()["status"]
                print(f"Vehicle 5 status: {v_status} (Expected: On Trip)")
                print(f"Driver 5 status: {d_status} (Expected: On Trip)")
                assert v_status == "On Trip"
                assert d_status == "On Trip"
    except Exception as e:
        print(f"FAILURE: Dispatch failed: {e}")
        sys.exit(1)

    # Test Case 2: Attempt dispatching already busy Vehicle/Driver
    print("\nTest Case 2: Attempting to dispatch already busy Vehicle 5 / Driver 5...")
    try:
        dispatch_trip(
            vehicle_id=5,
            driver_id=5,
            cargo_weight=1000.00,
            source="Austin, TX",
            destination="Houston, TX",
            planned_distance=160.00
        )
        print("FAILURE: Dispatch succeeded but should have raised ResourceUnavailableError!")
        sys.exit(1)
    except ResourceUnavailableError as e:
        print(f"SUCCESS: Caught expected exception: {e}")
    except Exception as e:
        print(f"FAILURE: Caught unexpected exception: {e}")
        sys.exit(1)

    # Test Case 3: Capacity Check
    print("\nTest Case 3: Attempting to dispatch weight (35,000 kg) exceeding Vehicle 5 max load capacity (30,000 kg)...")
    # Switch vehicle 5 & driver 5 back to Available for this test
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = 5")
            cur.execute("UPDATE drivers SET status = 'Available' WHERE id = 5")
    
    try:
        dispatch_trip(
            vehicle_id=5,
            driver_id=5,
            cargo_weight=35000.00,
            source="Austin, TX",
            destination="Houston, TX",
            planned_distance=160.00
        )
        print("FAILURE: Dispatch succeeded but should have raised CapacityExceededError!")
        sys.exit(1)
    except CapacityExceededError as e:
        print(f"SUCCESS: Caught expected exception: {e}")
    except Exception as e:
        print(f"FAILURE: Caught unexpected exception: {e}")
        sys.exit(1)

    # Test Case 4: Successful Trip Completion
    # Dispatch again first to have a dispatched trip
    trip = dispatch_trip(
        vehicle_id=5,
        driver_id=5,
        cargo_weight=10000.00,
        source="Austin, TX",
        destination="Dallas, TX",
        planned_distance=200.00,
        revenue=1200.00
    )
    trip_id = trip["id"]
    print(f"\nTest Case 4: Completing Trip ID {trip_id} (Current Vehicle 5 Odometer: 15000.00)...")
    try:
        completed = complete_trip(
            trip_id=trip_id,
            final_odometer=15200.50,
            fuel_consumed_liters=65.00
        )
        print(f"SUCCESS: Trip completed successfully! Final Odometer: {completed['final_odometer']}, Status: {completed['status']}")
        
        # Verify status in database
        with get_connection() as c:
            with c.cursor() as cur:
                cur.execute("SELECT status, odometer FROM vehicles WHERE id = 5")
                v = cur.fetchone()
                cur.execute("SELECT status FROM drivers WHERE id = 5")
                d_status = cur.fetchone()["status"]
                print(f"Vehicle 5 status: {v['status']} (Expected: Available), Odometer: {v['odometer']} (Expected: 15200.50)")
                print(f"Driver 5 status: {d_status} (Expected: Available)")
                assert v["status"] == "Available"
                assert float(v["odometer"]) == 15200.50
                assert d_status == "Available"
    except Exception as e:
        print(f"FAILURE: Completion failed: {e}")
        sys.exit(1)

    # Test Case 5: Invalid Odometer Reading Check
    # Dispatch again first
    trip = dispatch_trip(
        vehicle_id=5,
        driver_id=5,
        cargo_weight=10000.00,
        source="Austin, TX",
        destination="Dallas, TX",
        planned_distance=200.00,
        revenue=1200.00
    )
    trip_id = trip["id"]
    print(f"\nTest Case 5: Attempting to complete Trip ID {trip_id} with odometer less than current (15100.00 < 15200.50)...")
    try:
        complete_trip(
            trip_id=trip_id,
            final_odometer=15100.00,
            fuel_consumed_liters=40.00
        )
        print("FAILURE: Completion succeeded but should have raised InvalidOdometerError!")
        sys.exit(1)
    except InvalidOdometerError as e:
        print(f"SUCCESS: Caught expected exception: {e}")
    except Exception as e:
        print(f"FAILURE: Caught unexpected exception: {e}")
        sys.exit(1)

    # Clean up the dispatch we just did for Case 5, by cancelling it
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute("UPDATE trips SET status = 'Cancelled' WHERE id = %s", (trip_id,))
            cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = 5")
            cur.execute("UPDATE drivers SET status = 'Available' WHERE id = 5")

    # Test Case 6: ROI Aggregate Query Validation
    print("\nTest Case 6: Fetching Vehicle ROI calculations...")
    try:
        rois = calculate_vehicle_roi()
        print(f"{'Vehicle ID':<12} | {'Reg Number':<12} | {'Model':<25} | {'Acq Cost':<10} | {'Revenue':<10} | {'Maint':<10} | {'Fuel':<10} | {'ROI':<10}")
        print("-" * 115)
        for row in rois:
            print(f"{row['vehicle_id']:<12} | {row['registration_number']:<12} | {row['name_model']:<25} | {row['acquisition_cost']:<10} | {row['total_revenue']:<10} | {row['total_maintenance']:<10} | {row['total_fuel']:<10} | {row['roi']:<10}")
        print("\nAll unit tests passed successfully!")
    except Exception as e:
        print(f"FAILURE: ROI calculation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
