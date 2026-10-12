import sqlite3

from app import db


def fresh_db():
    conn = sqlite3.connect(":memory:")
    db.migrate(conn)
    return conn


def add_customer(conn, cid, email=None):
    conn.execute("INSERT INTO customers (id, email, name) VALUES (?, ?, ?)", (cid, email or f"c{cid}@example.com", f"C{cid}"))
