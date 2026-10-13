import os
import sqlite3
from typing import Iterator
 
DB_PATH = os.getenv("STUDENTS_DB", "students.db")
 
SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    date_of_birth   TEXT    NOT NULL,           -- ISO date YYYY-MM-DD
    email           TEXT    UNIQUE,
    phone           TEXT,
    course          TEXT,
    address         TEXT,
    enrollment_date TEXT,
    CHECK (email IS NOT NULL OR phone IS NOT NULL)
);
"""
 
 
def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
 
 
def get_conn() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()