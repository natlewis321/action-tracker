import csv
import io
from flask import Blueprint, request, redirect, url_for, render_template, flash, g

from routes.auth import login_required
from models.action import (
    list_actions as query_actions, get_action, create_action,
    update_action, get_comments, add_comment, get_audit_log,
)
from models.config import list_items
from models.user import list_users

actions_bp = Blueprint('actions', __name__, url_prefix='/actions')


def _get_form_options(db):
    return {
        'categories': list_items(db, 'categories'),
        'statuses': list_items(db, 'statuses'),
        'committees': list_items(db, 'committees'),
        'departments': list_items(db, 'departments'),
        'users': list_users(db),
    }


def _can_edit(user, action):
    if user['role'] == 'Admin':
        return True
    if user['role'] == 'Exec' and action['exec_sponsor_id'] == user['id']:
        return True
    if user['role'] == 'Owner' and action['owner_id'] == user['id']:
        return True
    return False


@actions_bp.route('/')
@login_required
def list_actions():
    db = g.db
    filters = {}
    for key in ('category_id', 'status_id', 'owner_id', 'exec_sponsor_id', 'committee_id', 'department_id'):
        val = request.args.get(key)
        if val:
            filters[key] = int(val)
    if request.args.get('overdue'):
        filters['overdue'] = True
    if request.args.get('search'):
        filters['search'] = request.args['search']

    actions = query_actions(db, filters if filters else None)
    options = _get_form_options(db)
    return render_template('actions/list.html', actions=actions, filters=request.args, **options)


@actions_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_action():
    db = g.db
    if g.user['role'] == 'Viewer':
        flash('You do not have permission to create actions.', 'danger')
        return redirect(url_for('actions.list_actions'))

    if request.method == 'POST':
        data = {k: request.form.get(k, '').strip() for k in (
            'title', 'description', 'category_id', 'source_committee_id',
            'reporting_committee_id', 'department_id', 'date_raised', 'due_date',
            'priority', 'status_id', 'owner_id', 'exec_sponsor_id',
        )}
        if not data['title'] or not data['category_id'] or not data['date_raised'] or not data['status_id']:
            flash('Title, category, date raised, and status are required.', 'danger')
        else:
            action_id = create_action(db, g.user['id'], data)
            flash('Action created.', 'success')
            return redirect(url_for('actions.detail', action_id=action_id))

    options = _get_form_options(db)
    return render_template('actions/form.html', action=None, **options)


@actions_bp.route('/<int:action_id>')
@login_required
def detail(action_id):
    db = g.db
    action = get_action(db, action_id)
    if not action:
        flash('Action not found.', 'danger')
        return redirect(url_for('actions.list_actions'))
    comments = get_comments(db, action_id)
    audit = get_audit_log(db, action_id)
    can_edit = _can_edit(g.user, action)
    return render_template('actions/detail.html', action=action, comments=comments,
                           audit=audit, can_edit=can_edit)


@actions_bp.route('/<int:action_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(action_id):
    db = g.db
    action = get_action(db, action_id)
    if not action:
        flash('Action not found.', 'danger')
        return redirect(url_for('actions.list_actions'))
    if not _can_edit(g.user, action):
        flash('You do not have permission to edit this action.', 'danger')
        return redirect(url_for('actions.detail', action_id=action_id))

    if request.method == 'POST':
        data = {k: request.form.get(k, '').strip() for k in (
            'title', 'description', 'category_id', 'source_committee_id',
            'reporting_committee_id', 'department_id', 'due_date',
            'priority', 'status_id', 'owner_id', 'exec_sponsor_id', 'closure_evidence',
        )}
        if not data['title'] or not data['category_id'] or not data['status_id']:
            flash('Title, category, and status are required.', 'danger')
        else:
            update_action(db, action_id, g.user['id'], data)
            flash('Action updated.', 'success')
            return redirect(url_for('actions.detail', action_id=action_id))
        action = get_action(db, action_id)

    options = _get_form_options(db)
    return render_template('actions/form.html', action=action, **options)


@actions_bp.route('/<int:action_id>/comment', methods=['POST'])
@login_required
def comment(action_id):
    body = request.form.get('body', '').strip()
    if body:
        add_comment(g.db, action_id, g.user['id'], body)
        flash('Comment added.', 'success')
    return redirect(url_for('actions.detail', action_id=action_id))


@actions_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_csv():
    if g.user['role'] not in ('Admin',):
        flash('Only admins can import actions.', 'danger')
        return redirect(url_for('actions.list_actions'))

    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename.endswith('.csv'):
            flash('Please upload a CSV file.', 'danger')
            return redirect(url_for('actions.import_csv'))

        db = g.db
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)

        # Build lookup maps for config values
        cat_map = {r['name'].lower(): r['id'] for r in list_items(db, 'categories')}
        status_map = {r['name'].lower(): r['id'] for r in list_items(db, 'statuses')}
        committee_map = {r['name'].lower(): r['id'] for r in list_items(db, 'committees')}
        dept_map = {r['name'].lower(): r['id'] for r in list_items(db, 'departments')}
        user_map = {r['email'].lower(): r['id'] for r in list_users(db)}

        imported, errors = 0, 0
        for i, row in enumerate(reader, start=2):
            title = row.get('title', '').strip()
            if not title:
                errors += 1
                continue
            cat_id = cat_map.get(row.get('category', '').strip().lower())
            status_id = status_map.get(row.get('status', '').strip().lower())
            if not cat_id or not status_id:
                errors += 1
                continue

            data = {
                'title': title,
                'description': row.get('description', '').strip(),
                'category_id': cat_id,
                'status_id': status_id,
                'source_committee_id': committee_map.get(row.get('source_committee', '').strip().lower()),
                'reporting_committee_id': committee_map.get(row.get('reporting_committee', '').strip().lower()),
                'department_id': dept_map.get(row.get('department', '').strip().lower()),
                'date_raised': row.get('date_raised', '').strip(),
                'due_date': row.get('due_date', '').strip(),
                'priority': row.get('priority', 'Medium').strip(),
                'owner_id': user_map.get(row.get('owner_email', '').strip().lower()),
                'exec_sponsor_id': user_map.get(row.get('exec_sponsor_email', '').strip().lower()),
            }
            if not data['date_raised']:
                errors += 1
                continue

            create_action(db, g.user['id'], data)
            imported += 1

        flash(f'Imported {imported} actions. {errors} rows skipped due to errors.', 'success' if imported else 'warning')
        return redirect(url_for('actions.list_actions'))

    return render_template('actions/import.html')
