import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_connection

def apply_seed():
    seed_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sql', 'seed.sql')
    with open(seed_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            print("Successfully seeded Indian dummy data.")
        conn.commit()

if __name__ == "__main__":
    apply_seed()
