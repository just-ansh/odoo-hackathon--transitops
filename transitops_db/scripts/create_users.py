"""
scripts/create_users.py
-----------------------
Seeds the `users` table with one account per TransitOps role.
Uses bcrypt to hash passwords — must be run AFTER schema.sql is applied.

Default credentials (change before any real deployment):
  fleet@transitops.com     / FleetMgr2024!   → Fleet Manager
  driver@transitops.com    / Driver2024!      → Driver
  safety@transitops.com    / Safety2024!      → Safety Officer
  finance@transitops.com   / Finance2024!     → Financial Analyst

Usage:
  python scripts/create_users.py
  python scripts/create_users.py --reset   (deletes existing users first)
"""

import sys
import os
import argparse

# Allow importing from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.auth import hash_password
from core.database import get_connection

USERS = [
    {
        "email": "fleet@transitops.com",
        "password": "FleetMgr2024!",
        "role": "Fleet Manager",
    },
    {
        "email": "driver@transitops.com",
        "password": "Driver2024!",
        "role": "Driver",
    },
    {
        "email": "safety@transitops.com",
        "password": "Safety2024!",
        "role": "Safety Officer",
    },
    {
        "email": "finance@transitops.com",
        "password": "Finance2024!",
        "role": "Financial Analyst",
    },
]


def create_users(reset: bool = False) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if reset:
                cur.execute("DELETE FROM users;")
                print("[!] Existing users deleted.")

            inserted = 0
            skipped = 0

            for user in USERS:
                hashed = hash_password(user["password"])
                try:
                    cur.execute(
                        """
                        INSERT INTO users (email, password_hash, role)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (email) DO NOTHING
                        RETURNING id
                        """,
                        (user["email"], hashed, user["role"]),
                    )
                    result = cur.fetchone()
                    if result:
                        print(f"  [OK]     Created : {user['email']}  [{user['role']}]")
                        inserted += 1
                    else:
                        print(f"  [SKIP]   Already exists: {user['email']}")
                        skipped += 1
                except Exception as e:
                    print(f"  [ERROR]  Failed to create {user['email']}: {e}")

            conn.commit()
            print(f"\n Done. {inserted} user(s) created, {skipped} skipped.")
            print("\n Login credentials:")
            print("  +-------------------------------------+--------------------+------------------+")
            print("  | Email                               | Password           | Role             |")
            print("  +-------------------------------------+--------------------+------------------+")
            for u in USERS:
                print(f"  | {u['email']:<35} | {u['password']:<18} | {u['role']:<16} |")
            print("  +-------------------------------------+--------------------+------------------+")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed TransitOps users into the database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing users before inserting.",
    )
    args = parser.parse_args()
    create_users(reset=args.reset)
