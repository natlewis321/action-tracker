from models.db import query_db

TABLES = {
    'categories': 'config_categories',
    'statuses': 'config_statuses',
    'committees': 'config_committees',
    'departments': 'config_departments',
}


def list_items(db, config_type, active_only=True):
    table = TABLES[config_type]
    order = 'sort_order, name' if config_type == 'statuses' else 'name'
    if active_only:
        return query_db(db, f"SELECT * FROM {table} WHERE is_active = 1 ORDER BY {order}")
    return query_db(db, f"SELECT * FROM {table} ORDER BY {order}")


def get_item(db, config_type, item_id):
    table = TABLES[config_type]
    return query_db(db, f"SELECT * FROM {table} WHERE id = ?", (item_id,), one=True)


def create_item(db, config_type, name, sort_order=None):
    table = TABLES[config_type]
    if config_type == 'statuses' and sort_order is not None:
        db.execute(f"INSERT INTO {table} (name, sort_order) VALUES (?, ?)", (name, sort_order))
    else:
        db.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
    db.commit()


def update_item(db, config_type, item_id, name, sort_order=None, is_active=1):
    table = TABLES[config_type]
    if config_type == 'statuses' and sort_order is not None:
        db.execute(f"UPDATE {table} SET name = ?, sort_order = ?, is_active = ? WHERE id = ?",
                   (name, sort_order, is_active, item_id))
    else:
        db.execute(f"UPDATE {table} SET name = ?, is_active = ? WHERE id = ?",
                   (name, is_active, item_id))
    db.commit()


def deactivate_item(db, config_type, item_id):
    table = TABLES[config_type]
    db.execute(f"UPDATE {table} SET is_active = 0 WHERE id = ?", (item_id,))
    db.commit()
