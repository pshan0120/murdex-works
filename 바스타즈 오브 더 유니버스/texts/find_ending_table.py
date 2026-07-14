import sys

murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

try:
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
except ImportError:
    print("Error: Could not import SharedConnectionPool.")
    sys.exit(1)

def explore_db():
    pool = SharedConnectionPool.get_instance()
    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        # Find tables related to ending
        cursor.execute("SHOW TABLES LIKE '%ending%'")
        tables = cursor.fetchall()
        for t in tables:
            print("Table:", list(t.values())[0])
            
            table_name = list(t.values())[0]
            cursor.execute(f"DESCRIBE {table_name}")
            cols = cursor.fetchall()
            print("Columns:", [c['Field'] for c in cols])
            print("---")

if __name__ == "__main__":
    explore_db()
