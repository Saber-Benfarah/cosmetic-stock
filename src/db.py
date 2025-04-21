# src/db.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../database/stock.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        name TEXT,
        description TEXT,
        expiration_date TEXT,
        image_path TEXT,
        category TEXT
    )
    """)
    conn.commit()
    conn.close()
