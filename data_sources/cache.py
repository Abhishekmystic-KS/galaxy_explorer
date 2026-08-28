import os
import sqlite3
import json

DB_PATH = "output/cache.db"

# Local database cache helper
def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_cache_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_cache (
            key TEXT PRIMARY KEY,
            value_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_cached_value(key: str) -> dict:
    try:
        init_cache_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value_json FROM api_cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row["value_json"])
    except Exception as e:
        print(f"Cache get error: {e}")
    return None

def set_cached_value(key: str, value: dict):
    try:
        init_cache_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO api_cache (key, value_json) VALUES (?, ?)",
            (key, json.dumps(value))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Cache set error: {e}")

# Pre-populated catalog of popular galaxies for offline/robust fallback
POPULAR_GALAXIES = {
    "m31": {
        "name": "M 31",
        "ra": 10.6847,
        "dec": 41.2687,
        "type": "Spiral Galaxy",
        "aliases": ["Andromeda Galaxy", "NGC 224", "MESSIER 031"],
        "redshift": -0.001001,
        "redshift_err": 0.000004,
        "mag": 3.44
    },
    "m51": {
        "name": "M 51",
        "ra": 202.4696,
        "dec": 47.1952,
        "type": "Spiral Galaxy",
        "aliases": ["Whirlpool Galaxy", "NGC 5194", "MESSIER 051"],
        "redshift": 0.001544,
        "redshift_err": 0.000005,
        "mag": 8.4
    },
    "ngc 4321": {
        "name": "NGC 4321",
        "ra": 185.7283,
        "dec": 15.8223,
        "type": "Spiral Galaxy",
        "aliases": ["M100", "MESSIER 100", "UGC 7450"],
        "redshift": 0.00524,
        "redshift_err": 0.00001,
        "mag": 10.1
    },
    "m81": {
        "name": "M 81",
        "ra": 148.8882,
        "dec": 69.0653,
        "type": "Spiral Galaxy",
        "aliases": ["Bode's Galaxy", "NGC 3031", "MESSIER 081"],
        "redshift": -0.000113,
        "redshift_err": 0.000004,
        "mag": 6.9
    },
    "m101": {
        "name": "M 101",
        "ra": 210.8023,
        "dec": 54.3490,
        "type": "Spiral Galaxy",
        "aliases": ["Pinwheel Galaxy", "NGC 5457", "MESSIER 101"],
        "redshift": 0.000804,
        "redshift_err": 0.000002,
        "mag": 7.86
    }
}

def resolve_popular_galaxy(query: str) -> dict:
    """Checks if query matches a known popular galaxy (case-insensitive name)."""
    norm_query = query.strip().lower().replace(" ", "")
    # Remove any dashes/underscores
    norm_query = norm_query.replace("-", "").replace("_", "")
    for k, v in POPULAR_GALAXIES.items():
        # Match base key or any alias
        matches = [k] + [a.strip().lower().replace(" ", "").replace("-", "") for a in v["aliases"]]
        if norm_query in matches:
            return v
    return None
