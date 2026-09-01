"""Seed the database with default config values and an admin user."""
import sys
from werkzeug.security import generate_password_hash
from models.db import init_db, get_db


def seed():
    init_db()
    db = get_db()

    defaults = {
        'config_categories': ['Committee', 'Internal Audit', 'Regulator', 'Other'],
        'config_statuses': [
            ('Recorded', 0),
            ('In Progress', 1),
            ('Completed', 2),
            ('Closed', 3),
        ],
    }

    for name in defaults['config_categories']:
        db.execute(
            "INSERT OR IGNORE INTO config_categories (name) VALUES (?)", (name,)
        )

    for name, sort_order in defaults['config_statuses']:
        db.execute(
            "INSERT OR IGNORE INTO config_statuses (name, sort_order) VALUES (?, ?)",
            (name, sort_order),
        )

    admin = db.execute("SELECT id FROM users WHERE email = ?", ('admin@local',)).fetchone()
    if not admin:
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ('Admin', 'admin@local', generate_password_hash('admin'), 'Admin'),
        )
        print("Created admin user: admin@local / admin")

    db.commit()
    db.close()
    print("Seed complete.")


if __name__ == '__main__':
    seed()
