import sqlite3

conn = sqlite3.connect("cargo.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    track_code TEXT,
    status TEXT DEFAULT 'Yolda',
    price INTEGER DEFAULT 0,
    weight REAL DEFAULT 0,
    paid INTEGER DEFAULT 0,
    pickup_point TEXT DEFAULT 'Pochta'
)
""")

conn.commit()
