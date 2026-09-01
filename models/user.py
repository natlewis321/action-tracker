from werkzeug.security import check_password_hash, generate_password_hash
from models.db import query_db


def authenticate(db, email, password):
    """Return user row if credentials are valid, else None."""
    user = query_db(db, "SELECT * FROM users WHERE email = ? AND is_active = 1", (email,), one=True)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None


def get_user_by_id(db, user_id):
    return query_db(db, "SELECT * FROM users WHERE id = ?", (user_id,), one=True)


def list_users(db, active_only=True):
    if active_only:
        return query_db(db, "SELECT * FROM users WHERE is_active = 1 ORDER BY name")
    return query_db(db, "SELECT * FROM users ORDER BY name")


def create_user(db, name, email, password, role, department=None):
    db.execute(
        "INSERT INTO users (name, email, password_hash, role, department) VALUES (?, ?, ?, ?, ?)",
        (name, email, generate_password_hash(password), role, department),
    )
    db.commit()


def update_user(db, user_id, **fields):
    allowed = {'name', 'email', 'role', 'department', 'is_active'}
    parts, vals = [], []
    for k, v in fields.items():
        if k in allowed:
            parts.append(f"{k} = ?")
            vals.append(v)
    if not parts:
        return
    parts.append("updated_at = datetime('now')")
    vals.append(user_id)
    db.execute(f"UPDATE users SET {', '.join(parts)} WHERE id = ?", vals)
    db.commit()


def reset_password(db, user_id, new_password):
    db.execute(
        "UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
        (generate_password_hash(new_password), user_id),
    )
    db.commit()
