"""SQLite access and migrations."""
import os
import sqlite3

MIGRATIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations")


def migrate(conn):
    """Apply every migrations/*.sql not yet recorded, in name order."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
    done = {r[0] for r in conn.execute("SELECT name FROM schema_migrations")}
    for name in sorted(os.listdir(MIGRATIONS)):
        if name.endswith(".sql") and name not in done:
            with open(os.path.join(MIGRATIONS, name)) as f:
                conn.executescript(f.read())
            conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (name,))
    conn.commit()


def connect(target):
    """Open a database file, or "replica" for a scratch copy of the prod snapshot."""
    if target == "replica":
        from ops.replica import open_copy
        conn = open_copy()
    else:
        conn = sqlite3.connect(target)
    migrate(conn)
    return conn
