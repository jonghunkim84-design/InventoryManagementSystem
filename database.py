import sqlite3
from contextlib import contextmanager

DB_PATH = "inventory.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS ingredients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    current_stock REAL DEFAULT 0,
    base_unit TEXT NOT NULL,
    safety_stock REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ingredient_conversions (
    id TEXT PRIMARY KEY,
    ingredient_id TEXT NOT NULL,
    unit_name TEXT NOT NULL,
    conversion_factor REAL NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

CREATE TABLE IF NOT EXISTS incoming_logs (
    id TEXT PRIMARY KEY,
    ingredient_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    total_price INTEGER,
    scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

CREATE TABLE IF NOT EXISTS recipes (
    id TEXT PRIMARY KEY,
    menu_name TEXT NOT NULL,
    ingredient_id TEXT NOT NULL,
    usage_amount REAL NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

CREATE TABLE IF NOT EXISTS waste_logs (
    id TEXT PRIMARY KEY,
    ingredient_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

CREATE TABLE IF NOT EXISTS inventory_adjustments (
    id TEXT PRIMARY KEY,
    ingredient_id TEXT NOT NULL,
    adjustment_amount REAL NOT NULL,
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);
"""


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
