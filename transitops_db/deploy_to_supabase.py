"""
TransitOps Supabase Deployment Script (deploy_to_supabase.py)
-----------------------------------------------------------
This script deploys the database schema and seed data directly to your
Supabase PostgreSQL instance, then runs transaction verification tests.

Usage:
  PowerShell:
    $env:DATABASE_URL="postgresql://postgres:<your-password>@db.<your-project-ref>.supabase.co:5432/postgres"
    .\venv\Scripts\python .\transitops_db\deploy_to_supabase.py
"""

import os
import sys
import psycopg
from database import (
    get_connection,
    dispatch_trip,
    complete_trip,
    calculate_vehicle_roi,
    ResourceUnavailableError,
    CapacityExceededError,
    InvalidOdometerError,
    InvalidStatusTransitionError
)

def run_sql_file(conn, file_path: str):
    """Utility to execute all SQL commands from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"Applied SQL script: {os.path.basename(file_path)}")

def main():
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("[ERROR] DATABASE_URL environment variable is not set.")
        print("Please set your Supabase connection string. Example:")
        print('  $env:DATABASE_URL="postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"')
        sys.exit(1)
        
    print("Connecting to Supabase database...")
    try:
        conn = get_connection(conn_string)
        print("SUCCESS: Connected to Supabase!")
    except Exception as e:
        print(f"[ERROR] Connection to Supabase failed: {e}")
        sys.exit(1)
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(base_dir, "schema.sql")
    seed_file = os.path.join(base_dir, "seed.sql")
    
    # 1. Apply Schema and Seed
    try:
        print("\n--- Initializing Schema and Seeding Data on Supabase ---")
        run_sql_file(conn, schema_file)
        run_sql_file(conn, seed_file)
        conn.close()
        print("SUCCESS: Database schema and seed data deployed to Supabase.")
    except Exception as e:
        print(f"[ERROR] Failed to run schema/seed on Supabase: {e}")
        sys.exit(1)

    print("\n--- Starting Supabase Transaction Verification ---")
    
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
            revenue=1400.00,
            conn_string=conn_string
        )
        print(f"SUCCESS: Trip dispatched on Supabase! Trip ID: {trip['id']}, Status: {trip['status']}")
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
            planned_distance=160.00,
            conn_string=conn_string
        )
        print("FAILURE: Dispatch succeeded but should have raised ResourceUnavailableError!")
        sys.exit(1)
    except ResourceUnavailableError as e:
        print(f"SUCCESS: Caught expected exception: {e}")
    except Exception as e:
        print(f"FAILURE: Caught unexpected exception: {e}")
        sys.exit(1)

    # Test Case 3: Capacity Check
    print("\nTest Case 3: Attempting to dispatch weight (35,000 kg) exceeding Vehicle 5 capacity...")
    # Reset vehicle/driver to Available
    with get_connection(conn_string) as c:
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
            planned_distance=160.00,
            conn_string=conn_string
        )
        print("FAILURE: Dispatch succeeded but should have raised CapacityExceededError!")
        sys.exit(1)
    except CapacityExceededError as e:
        print(f"SUCCESS: Caught expected exception: {e}")
    except Exception as e:
        print(f"FAILURE: Caught unexpected exception: {e}")
        sys.exit(1)

    # Test Case 4: Successful Trip Completion
    trip = dispatch_trip(
        vehicle_id=5,
        driver_id=5,
        cargo_weight=10000.00,
        source="Austin, TX",
        destination="Dallas, TX",
        planned_distance=200.00,
        revenue=1200.00,
        conn_string=conn_string
    )
    trip_id = trip["id"]
    print(f"\nTest Case 4: Completing Trip ID {trip_id} on Supabase...")
    try:
        completed = complete_trip(
            trip_id=trip_id,
            final_odometer=15200.50,
            fuel_consumed_liters=65.00,
            conn_string=conn_string
        )
        print(f"SUCCESS: Trip completed on Supabase! Odometer updated to: {completed['final_odometer']}")
    except Exception as e:
        print(f"FAILURE: Completion failed: {e}")
        sys.exit(1)

    # Test Case 5: ROI Aggregate Query Validation
    print("\nTest Case 5: Fetching Vehicle ROI calculations from Supabase...")
    try:
        rois = calculate_vehicle_roi(conn_string=conn_string)
        print(f"{'Vehicle ID':<12} | {'Reg Number':<12} | {'Model':<25} | {'Acq Cost':<10} | {'Revenue':<10} | {'Maint':<10} | {'Fuel':<10} | {'ROI':<10}")
        print("-" * 115)
        for row in rois:
            print(f"{row['vehicle_id']:<12} | {row['registration_number']:<12} | {row['name_model']:<25} | {row['acquisition_cost']:<10} | {row['total_revenue']:<10} | {row['total_maintenance']:<10} | {row['total_fuel']:<10} | {row['roi']:<10}")
        print("\nAll Supabase transactions and queries verified successfully!")
    except Exception as e:
        print(f"FAILURE: ROI calculation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
