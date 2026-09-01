from datetime import date
from flask import Blueprint, render_template, g, jsonify, request

from routes.auth import login_required
from models.db import query_db
from models.config import list_items

dashboard_bp = Blueprint('dashboard', __name__)


def _build_filter(alias='a'):
    """Build WHERE clauses and params from committee_id/department_id query args."""
    wheres, params = [], []
    committee_id = request.args.get('committee_id', type=int)
    department_id = request.args.get('department_id', type=int)
    if committee_id:
        wheres.append(f"({alias}.source_committee_id = ? OR {alias}.reporting_committee_id = ?)")
        params.extend([committee_id, committee_id])
    if department_id:
        wheres.append(f"{alias}.department_id = ?")
        params.append(department_id)
    return wheres, params


def _where_sql(extra_wheres=None, extra_params=None):
    """Combine filter clauses with optional extra conditions."""
    wheres, params = _build_filter()
    if extra_wheres:
        wheres.extend(extra_wheres)
    if extra_params:
        params.extend(extra_params)
    clause = (" WHERE " + " AND ".join(wheres)) if wheres else ""
    return clause, params


@dashboard_bp.route('/')
@login_required
def index():
    db = g.db
    today = date.today().isoformat()
    fw, fp = _build_filter()
    filter_clause = (" AND " + " AND ".join(fw)) if fw else ""

    total = query_db(db, f"SELECT COUNT(*) AS n FROM actions a WHERE 1=1 {filter_clause}", fp, one=True)['n']
    open_count = query_db(db, f"""
        SELECT COUNT(*) AS n FROM actions a
        JOIN config_statuses s ON a.status_id = s.id
        WHERE s.name NOT IN ('Completed','Closed') {filter_clause}
    """, fp, one=True)['n']
    closed_count = query_db(db, f"""
        SELECT COUNT(*) AS n FROM actions a
        JOIN config_statuses s ON a.status_id = s.id
        WHERE s.name IN ('Completed','Closed') {filter_clause}
    """, fp, one=True)['n']
    overdue = query_db(db, f"""
        SELECT COUNT(*) AS n FROM actions a
        JOIN config_statuses s ON a.status_id = s.id
        WHERE a.due_date < ? AND s.name NOT IN ('Completed','Closed') {filter_clause}
    """, [today] + fp, one=True)['n']
    due_soon = query_db(db, f"""
        SELECT COUNT(*) AS n FROM actions a
        JOIN config_statuses s ON a.status_id = s.id
        WHERE a.due_date BETWEEN ? AND date(?, '+14 days')
        AND s.name NOT IN ('Completed','Closed') {filter_clause}
    """, [today, today] + fp, one=True)['n']

    committees = list_items(db, 'committees')
    departments = list_items(db, 'departments')

    return render_template('dashboard.html',
                           total=total, open_count=open_count, closed_count=closed_count,
                           overdue=overdue, due_soon=due_soon,
                           committees=committees, departments=departments,
                           selected_committee=request.args.get('committee_id', ''),
                           selected_department=request.args.get('department_id', ''),
                           today=today)


@dashboard_bp.route('/api/chart-data')
@login_required
def chart_data():
    db = g.db
    today = date.today().isoformat()
    fw, fp = _build_filter()
    fc = (" AND " + " AND ".join(fw)) if fw else ""

    by_status = query_db(db, f"""
        SELECT s.name, COUNT(*) AS count
        FROM actions a JOIN config_statuses s ON a.status_id = s.id
        WHERE 1=1 {fc}
        GROUP BY s.name ORDER BY s.sort_order
    """, fp)

    by_category = query_db(db, f"""
        SELECT c.name, COUNT(*) AS count
        FROM actions a JOIN config_categories c ON a.category_id = c.id
        WHERE 1=1 {fc}
        GROUP BY c.name ORDER BY c.name
    """, fp)

    by_priority = query_db(db, f"""
        SELECT a.priority, COUNT(*) AS count FROM actions a
        WHERE 1=1 {fc}
        GROUP BY a.priority
    """, fp)

    by_committee = query_db(db, f"""
        SELECT COALESCE(rc.name, 'Unassigned') AS name, COUNT(*) AS count
        FROM actions a LEFT JOIN config_committees rc ON a.reporting_committee_id = rc.id
        WHERE 1=1 {fc}
        GROUP BY rc.name ORDER BY rc.name
    """, fp)

    ageing = query_db(db, f"""
        SELECT
            CASE
                WHEN julianday('now') - julianday(a.date_raised) <= 30 THEN '0-30 days'
                WHEN julianday('now') - julianday(a.date_raised) <= 60 THEN '31-60 days'
                WHEN julianday('now') - julianday(a.date_raised) <= 90 THEN '61-90 days'
                ELSE '90+ days'
            END AS band,
            COUNT(*) AS count
        FROM actions a
        JOIN config_statuses s ON a.status_id = s.id
        WHERE s.name NOT IN ('Completed','Closed') {fc}
        GROUP BY band
    """, fp)

    overdue_by_owner = query_db(db, f"""
        SELECT COALESCE(u.name, 'Unassigned') AS name, COUNT(*) AS count
        FROM actions a
        JOIN config_statuses s ON a.status_id = s.id
        LEFT JOIN users u ON a.owner_id = u.id
        WHERE a.due_date < ? AND s.name NOT IN ('Completed','Closed') {fc}
        GROUP BY u.name ORDER BY count DESC
    """, [today] + fp)

    return jsonify({
        'by_status': [dict(r) for r in by_status],
        'by_category': [dict(r) for r in by_category],
        'by_priority': [dict(r) for r in by_priority],
        'by_committee': [dict(r) for r in by_committee],
        'ageing': [dict(r) for r in ageing],
        'overdue_by_owner': [dict(r) for r in overdue_by_owner],
    })
