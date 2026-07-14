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
        cursor.execute("DESCRIBE clue")
        cols = cursor.fetchall()
        print("clue table columns:", [c['Field'] for c in cols])
        
        cursor.execute("DESCRIBE clue_variant")
        cols = cursor.fetchall()
        print("clue_variant table columns:", [c['Field'] for c in cols])

if __name__ == "__main__":
    explore_db()
