import csv
import io
from datetime import date, datetime

from flask import Blueprint, request, render_template, g, make_response
from fpdf import FPDF

from routes.auth import login_required
from models.action import list_actions
from models.config import list_items
from models.user import list_users
from models.db import query_db

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


def _get_actions(db, filters):
    f = {}
    if filters.get('category_id'):
        f['category_id'] = int(filters['category_id'])
    if filters.get('status_id'):
        f['status_id'] = int(filters['status_id'])
    if filters.get('committee_id'):
        f['committee_id'] = int(filters['committee_id'])
    if filters.get('owner_id'):
        f['owner_id'] = int(filters['owner_id'])
    if filters.get('exec_sponsor_id'):
        f['exec_sponsor_id'] = int(filters['exec_sponsor_id'])
    if filters.get('department_id'):
        f['department_id'] = int(filters['department_id'])
    if filters.get('overdue'):
        f['overdue'] = True
    return list_actions(db, f if f else None)


@reports_bp.route('/')
@login_required
def index():
    db = g.db
    return render_template('reports/export.html',
                           categories=list_items(db, 'categories'),
                           statuses=list_items(db, 'statuses'),
                           committees=list_items(db, 'committees'),
                           departments=list_items(db, 'departments'),
                           users=list_users(db))


@reports_bp.route('/csv')
@login_required
def export_csv():
    db = g.db
    actions = _get_actions(db, request.args)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Title', 'Description', 'Category', 'Status', 'Priority',
                     'Source Committee', 'Reporting Committee', 'Department',
                     'Owner', 'Exec Sponsor', 'Date Raised', 'Due Date',
                     'Closure Evidence', 'Created At', 'Updated At'])
    for a in actions:
        writer.writerow([
            a['id'], a['title'], a['description'] or '', a['category_name'],
            a['status_name'], a['priority'],
            a['source_committee_name'] or '', a['reporting_committee_name'] or '',
            a['department_name'] or '',
            a['owner_name'] or '', a['exec_sponsor_name'] or '',
            a['date_raised'], a['due_date'] or '',
            a['closure_evidence'] or '', a['created_at'], a['updated_at'],
        ])

    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
    resp.headers['Content-Disposition'] = f'attachment; filename=actions_export_{date.today().isoformat()}.csv'
    return resp


@reports_bp.route('/pdf')
@login_required
def export_pdf():
    db = g.db
    actions = _get_actions(db, request.args)

    committee_name = 'All'
    if request.args.get('committee_id'):
        c = query_db(db, "SELECT name FROM config_committees WHERE id = ?",
                     (int(request.args['committee_id']),), one=True)
        if c:
            committee_name = c['name']

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Action Tracker Report', ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f'Committee: {committee_name}  |  Generated: {datetime.now().strftime("%d %b %Y %H:%M")}', ln=True)
    pdf.ln(4)

    headers = ['ID', 'Title', 'Category', 'Status', 'Priority', 'Owner', 'Due Date', 'Raised']
    widths = [12, 80, 30, 25, 20, 35, 25, 25]

    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_fill_color(44, 62, 128)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 7, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(0, 0, 0)
    for a in actions:
        if pdf.get_y() > 180:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_fill_color(44, 62, 128)
            pdf.set_text_color(255, 255, 255)
            for i, h in enumerate(headers):
                pdf.cell(widths[i], 7, h, border=1, fill=True)
            pdf.ln()
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(0, 0, 0)

        row = [
            str(a['id']),
            (a['title'][:40] + '...' if len(a['title']) > 43 else a['title']),
            a['category_name'],
            a['status_name'],
            a['priority'],
            a['owner_name'] or '-',
            a['due_date'] or '-',
            a['date_raised'],
        ]
        for i, val in enumerate(row):
            pdf.cell(widths[i], 6, val, border=1)
        pdf.ln()

    summary_total = len(actions)
    overdue_count = sum(1 for a in actions if a['due_date'] and a['due_date'] < date.today().isoformat()
                        and a['status_name'] not in ('Completed', 'Closed'))
    pdf.ln(6)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 6, f'Total: {summary_total}  |  Overdue: {overdue_count}', ln=True)

    resp = make_response(pdf.output())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'attachment; filename=actions_report_{date.today().isoformat()}.pdf'
    return resp
