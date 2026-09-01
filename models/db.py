import sqlite3
import os
import config


def get_db():
    """Get a database connection with row factory enabled."""
    db = sqlite3.connect(config.DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    """Create tables from schema.sql if they don't exist."""
    schema_path = os.path.join(config.BASE_DIR, 'schema.sql')
    db = get_db()
    with open(schema_path, 'r') as f:
        db.executescript(f.read())
    db.close()


def query_db(db, sql, args=(), one=False):
    """Execute a query and return results as Row objects."""
    cur = db.execute(sql, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv
