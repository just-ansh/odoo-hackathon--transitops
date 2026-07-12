"""
scripts/seed_demo_data.py
-------------------------
Seeds the TransitOps database with a rich set of 30 mock vehicles,
multiple drivers, completed trips, fuel logs, and expenses to populate
all dashboard widgets and reports charts.

Usage:
  python scripts/seed_demo_data.py
"""

import sys
import os
import random
from datetime import datetime, timedelta, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_connection

VEHICLE_MODELS = {
    "Truck": ["Ford F-550 Super Duty", "Chevrolet Silverado 5500HD", "Ram 5500", "Isuzu NPR-HD", "Freightliner M2 106"],
    "Van": ["Ford Transit Cargo", "Mercedes-Benz Sprinter", "Ram ProMaster", "Chevrolet Express 3500"],
    "Trailer": ["Great Dane Dry Van", "Wabash National Trailer", "Utility Dry Freight"],
    "Refrigerated": ["Thermo King Reefer", "Carrier Transicold Reefer", "Hyundai Translead Reefer"]
}

REGIONS = ["Delhi NCR", "Mumbai Region", "Bangalore South", "Chennai Coastal", "Kolkata East"]
VEHICLE_STATUSES = ["Available", "On Trip", "In Shop", "Retired"]
DRIVER_STATUSES = ["Available", "On Trip", "Off Duty", "Suspended"]

CITIES = ["Delhi", "Noida", "Gurugram", "Mumbai", "Pune", "Thane", "Bangalore", "Mysore", "Chennai", "Kolkata"]

def seed_data():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("Cleaning up old demo data...")
            cur.execute("DELETE FROM expenses;")
            cur.execute("DELETE FROM fuel_logs;")
            cur.execute("DELETE FROM trips;")
            cur.execute("DELETE FROM drivers;")
            cur.execute("DELETE FROM vehicles;")
            
            print("Seeding 30 vehicles...")
            vehicles = []
            for i in range(1, 31):
                v_type = random.choice(list(VEHICLE_MODELS.keys()))
                model = random.choice(VEHICLE_MODELS[v_type])
                reg_num = f"DL-{random.randint(10, 99)}-{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}-{random.randint(1000, 9999)}"
                capacity = random.randint(1000, 15000) if v_type != "Van" else random.randint(500, 2000)
                odometer = random.randint(5000, 150000)
                acq_cost = random.randint(30000, 120000)
                status = random.choice(VEHICLE_STATUSES)
                region = random.choice(REGIONS)
                
                cur.execute(
                    """
                    INSERT INTO vehicles 
                        (registration_number, name_model, type, max_load_capacity, odometer, acquisition_cost, status, region)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, registration_number, name_model, type, odometer, acquisition_cost
                    """,
                    (reg_num, f"{model} #{i}", v_type, capacity, odometer, acq_cost, status, region)
                )
                vehicles.append(cur.fetchone())

            print("Seeding 15 drivers...")
            drivers = []
            first_names = ["Arjun", "Amit", "Vijay", "Rahul", "Sanjay", "Anil", "Vikram", "Rajesh", "Sunil", "Prakash", "Sandeep", "Manoj", "Rakesh", "Rohan", "Karan"]
            last_names = ["Sharma", "Verma", "Kumar", "Singh", "Yadav", "Patel", "Joshi", "Gupta", "Reddy", "Nair"]
            for i in range(15):
                name = f"{random.choice(first_names)} {random.choice(last_names)}"
                lic_num = f"DL{random.randint(10000000, 99999999)}"
                category = "Class A CDL" if i % 2 == 0 else "Class B CDL"
                expiry = date.today() + timedelta(days=random.randint(-10, 730))
                contact = f"+91-{random.randint(90000, 99999)}-{random.randint(10000, 99999)}"
                score = round(random.uniform(70.0, 100.0), 2)
                status = random.choice(DRIVER_STATUSES)
                
                cur.execute(
                    """
                    INSERT INTO drivers 
                        (name, license_number, license_category, license_expiry_date, contact_number, safety_score, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, name
                    """,
                    (name, lic_num, category, expiry, contact, score, status)
                )
                drivers.append(cur.fetchone())

            print("Seeding 80 trips...")
            # We want completed trips spread across the last 6 months to make monthly graphs look awesome
            today_dt = datetime.now()
            for i in range(80):
                v = random.choice(vehicles)
                d = random.choice(drivers)
                source = random.choice(CITIES)
                dest = random.choice([c for c in CITIES if c != source])
                weight = random.randint(200, 5000)
                distance = random.randint(50, 600)
                revenue = distance * random.randint(4, 12)
                
                # Completed state for most, some active, some draft
                status = "Completed"
                if i < 5:
                    status = "Draft"
                elif i < 12:
                    status = "Dispatched"
                    
                # Subtract days randomly to distribute over 6 months
                trip_date = today_dt - timedelta(days=random.randint(0, 170))
                
                final_odo = None
                fuel_liters = None
                if status == "Completed":
                    final_odo = float(v["odometer"]) + distance
                    fuel_liters = round(distance / random.uniform(5.0, 12.0), 2)
                
                cur.execute(
                    """
                    INSERT INTO trips 
                        (source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, final_odometer, fuel_consumed_liters, revenue, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, vehicle_id, revenue
                    """,
                    (source, dest, v["id"], d["id"], weight, distance, final_odo, fuel_liters, revenue, status, trip_date)
                )
                trip = cur.fetchone()
                
                # If completed, add fuel log and maybe an expense
                if status == "Completed":
                    # Fuel cost
                    fuel_cost = fuel_liters * random.uniform(1.2, 1.8)
                    cur.execute(
                        """
                        INSERT INTO fuel_logs (vehicle_id, trip_id, liters, cost, logged_date)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (v["id"], trip["id"], fuel_liters, fuel_cost, trip_date.date())
                    )
                    
                    # 40% chance of Tolls or Other expenses
                    if random.random() < 0.4:
                        exp_type = random.choice(["Tolls", "Other"])
                        amount = random.randint(10, 150)
                        desc = "Highway toll tax" if exp_type == "Tolls" else "Minor container strapping repairs"
                        cur.execute(
                            """
                            INSERT INTO expenses (vehicle_id, type, amount, description, logged_date)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (v["id"], exp_type, amount, desc, trip_date.date())
                        )
            
            print("Seeding maintenance logs...")
            for v in vehicles:
                # 50% chance vehicle has maintenance history
                if random.random() < 0.5:
                    maint_date = today_dt - timedelta(days=random.randint(10, 100))
                    cost = random.randint(150, 1200)
                    cur.execute(
                        """
                        INSERT INTO maintenance_logs (vehicle_id, description, cost, status, logged_at, closed_at)
                        VALUES (%s, %s, %s, 'Closed', %s, %s)
                        """,
                        (v["id"], "Scheduled preventative engine maintenance and filter swaps", cost, maint_date, maint_date + timedelta(days=random.randint(1, 3)))
                    )

            conn.commit()
            print("\n[OK] Seeding completed successfully!")
            print(f"  - 30 Vehicles created")
            print(f"  - 15 Drivers created")
            print(f"  - 80 Trips created (distributed over last 6 months)")
            print(f"  - Fuel & Expense transactions correctly linked and simulated")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Seeding failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_data()
