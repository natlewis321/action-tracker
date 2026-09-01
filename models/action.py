from models.db import query_db


def _log_changes(db, action_id, user_id, old_row, new_fields):
    """Record each changed field in the audit log."""
    for field, new_val in new_fields.items():
        old_val = old_row[field] if old_row and field in old_row.keys() else None
        if str(old_val) != str(new_val):
            db.execute(
                "INSERT INTO audit_log (action_id, user_id, field_name, old_value, new_value) VALUES (?, ?, ?, ?, ?)",
                (action_id, user_id, field, str(old_val) if old_val is not None else None, str(new_val)),
            )


def get_action(db, action_id):
    return query_db(db, """
        SELECT a.*,
               c.name AS category_name,
               s.name AS status_name,
               sc.name AS source_committee_name,
               rc.name AS reporting_committee_name,
               d.name AS department_name,
               o.name AS owner_name,
               e.name AS exec_sponsor_name,
               cb.name AS created_by_name,
               clb.name AS closed_by_name
        FROM actions a
        LEFT JOIN config_categories c ON a.category_id = c.id
        LEFT JOIN config_statuses s ON a.status_id = s.id
        LEFT JOIN config_committees sc ON a.source_committee_id = sc.id
        LEFT JOIN config_committees rc ON a.reporting_committee_id = rc.id
        LEFT JOIN config_departments d ON a.department_id = d.id
        LEFT JOIN users o ON a.owner_id = o.id
        LEFT JOIN users e ON a.exec_sponsor_id = e.id
        LEFT JOIN users cb ON a.created_by_id = cb.id
        LEFT JOIN users clb ON a.closed_by_id = clb.id
        WHERE a.id = ?
    """, (action_id,), one=True)


def list_actions(db, filters=None):
    sql = """
        SELECT a.*,
               c.name AS category_name,
               s.name AS status_name,
               s.sort_order AS status_order,
               sc.name AS source_committee_name,
               rc.name AS reporting_committee_name,
               d.name AS department_name,
               o.name AS owner_name,
               e.name AS exec_sponsor_name
        FROM actions a
        LEFT JOIN config_categories c ON a.category_id = c.id
        LEFT JOIN config_statuses s ON a.status_id = s.id
        LEFT JOIN config_committees sc ON a.source_committee_id = sc.id
        LEFT JOIN config_committees rc ON a.reporting_committee_id = rc.id
        LEFT JOIN config_departments d ON a.department_id = d.id
        LEFT JOIN users o ON a.owner_id = o.id
        LEFT JOIN users e ON a.exec_sponsor_id = e.id
    """
    wheres, params = [], []
    if filters:
        if filters.get('category_id'):
            wheres.append("a.category_id = ?")
            params.append(filters['category_id'])
        if filters.get('status_id'):
            wheres.append("a.status_id = ?")
            params.append(filters['status_id'])
        if filters.get('owner_id'):
            wheres.append("a.owner_id = ?")
            params.append(filters['owner_id'])
        if filters.get('exec_sponsor_id'):
            wheres.append("a.exec_sponsor_id = ?")
            params.append(filters['exec_sponsor_id'])
        if filters.get('committee_id'):
            wheres.append("(a.source_committee_id = ? OR a.reporting_committee_id = ?)")
            params.extend([filters['committee_id'], filters['committee_id']])
        if filters.get('department_id'):
            wheres.append("a.department_id = ?")
            params.append(filters['department_id'])
        if filters.get('overdue'):
            wheres.append("a.due_date < date('now') AND s.name NOT IN ('Completed','Closed')")
        if filters.get('search'):
            wheres.append("(a.title LIKE ? OR a.description LIKE ?)")
            term = f"%{filters['search']}%"
            params.extend([term, term])

    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += " ORDER BY s.sort_order ASC, a.due_date ASC"
    return query_db(db, sql, params)


def create_action(db, user_id, data):
    cur = db.execute("""
        INSERT INTO actions (title, description, category_id, source_committee_id,
            reporting_committee_id, department_id, date_raised, due_date, priority,
            status_id, owner_id, exec_sponsor_id, created_by_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['title'], data.get('description'), data['category_id'],
        data.get('source_committee_id') or None,
        data.get('reporting_committee_id') or None,
        data.get('department_id') or None,
        data['date_raised'], data.get('due_date') or None,
        data.get('priority', 'Medium'), data['status_id'],
        data.get('owner_id') or None,
        data.get('exec_sponsor_id') or None,
        user_id,
    ))
    action_id = cur.lastrowid
    db.execute(
        "INSERT INTO audit_log (action_id, user_id, field_name, old_value, new_value) VALUES (?, ?, ?, ?, ?)",
        (action_id, user_id, 'created', None, 'Action created'),
    )
    db.commit()
    return action_id


def update_action(db, action_id, user_id, data):
    old = query_db(db, "SELECT * FROM actions WHERE id = ?", (action_id,), one=True)
    if not old:
        return False

    fields = {
        'title': data['title'],
        'description': data.get('description'),
        'category_id': data['category_id'],
        'source_committee_id': data.get('source_committee_id') or None,
        'reporting_committee_id': data.get('reporting_committee_id') or None,
        'department_id': data.get('department_id') or None,
        'due_date': data.get('due_date') or None,
        'priority': data.get('priority', 'Medium'),
        'status_id': data['status_id'],
        'owner_id': data.get('owner_id') or None,
        'exec_sponsor_id': data.get('exec_sponsor_id') or None,
    }

    closure_evidence = data.get('closure_evidence')
    if closure_evidence:
        fields['closure_evidence'] = closure_evidence

    status = query_db(db, "SELECT name FROM config_statuses WHERE id = ?", (data['status_id'],), one=True)
    if status and status['name'] == 'Closed' and old['status_id'] != data['status_id']:
        fields['closed_by_id'] = user_id
        fields['closed_at'] = "datetime('now')"

    _log_changes(db, action_id, user_id, old, fields)

    set_parts = [f"{k} = ?" for k in fields]
    set_parts.append("updated_at = datetime('now')")
    vals = list(fields.values())
    vals.append(action_id)

    db.execute(f"UPDATE actions SET {', '.join(set_parts)} WHERE id = ?", vals)
    db.commit()
    return True


def get_comments(db, action_id):
    return query_db(db, """
        SELECT ac.*, u.name AS user_name
        FROM action_comments ac
        JOIN users u ON ac.user_id = u.id
        WHERE ac.action_id = ?
        ORDER BY ac.created_at ASC
    """, (action_id,))


def add_comment(db, action_id, user_id, body):
    db.execute(
        "INSERT INTO action_comments (action_id, user_id, body) VALUES (?, ?, ?)",
        (action_id, user_id, body),
    )
    db.commit()


def get_audit_log(db, action_id):
    return query_db(db, """
        SELECT al.*, u.name AS user_name
        FROM audit_log al
        JOIN users u ON al.user_id = u.id
        WHERE al.action_id = ?
        ORDER BY al.changed_at DESC
    """, (action_id,))
