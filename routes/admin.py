from flask import Blueprint, request, redirect, url_for, render_template, flash, g

from routes.auth import role_required
from models.user import list_users, create_user, update_user, reset_password, get_user_by_id
from models.config import list_items, create_item, update_item, deactivate_item, get_item, TABLES

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@role_required('Admin')
def users_list():
    users = list_users(g.db, active_only=False)
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@role_required('Admin')
def user_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'Viewer')
        department = request.form.get('department', '').strip() or None
        if not name or not email or not password:
            flash('Name, email, and password are required.', 'danger')
        else:
            try:
                create_user(g.db, name, email, password, role, department)
                flash(f'User {name} created.', 'success')
                return redirect(url_for('admin.users_list'))
            except Exception:
                flash('A user with that email already exists.', 'danger')
    return render_template('admin/user_form.html', user=None)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@role_required('Admin')
def user_edit(user_id):
    user = get_user_by_id(g.db, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users_list'))
    if request.method == 'POST':
        fields = {
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'role': request.form.get('role', 'Viewer'),
            'department': request.form.get('department', '').strip() or None,
            'is_active': 1 if request.form.get('is_active') else 0,
        }
        update_user(g.db, user_id, **fields)
        new_pw = request.form.get('new_password', '').strip()
        if new_pw:
            reset_password(g.db, user_id, new_pw)
        flash('User updated.', 'success')
        return redirect(url_for('admin.users_list'))
    return render_template('admin/user_form.html', user=user)


@admin_bp.route('/config')
@role_required('Admin')
def config_list():
    data = {}
    for key in TABLES:
        data[key] = list_items(g.db, key, active_only=False)
    return render_template('admin/config.html', data=data)


@admin_bp.route('/config/<config_type>/add', methods=['POST'])
@role_required('Admin')
def config_add(config_type):
    if config_type not in TABLES:
        flash('Invalid config type.', 'danger')
        return redirect(url_for('admin.config_list'))
    name = request.form.get('name', '').strip()
    sort_order = request.form.get('sort_order', '0').strip()
    if not name:
        flash('Name is required.', 'danger')
    else:
        try:
            create_item(g.db, config_type, name, int(sort_order) if sort_order else 0)
            flash(f'Added "{name}".', 'success')
        except Exception:
            flash(f'"{name}" already exists.', 'danger')
    return redirect(url_for('admin.config_list'))


@admin_bp.route('/config/<config_type>/<int:item_id>/edit', methods=['POST'])
@role_required('Admin')
def config_edit(config_type, item_id):
    if config_type not in TABLES:
        flash('Invalid config type.', 'danger')
        return redirect(url_for('admin.config_list'))
    name = request.form.get('name', '').strip()
    sort_order = request.form.get('sort_order', '0').strip()
    is_active = 1 if request.form.get('is_active') else 0
    if name:
        update_item(g.db, config_type, item_id, name, int(sort_order) if sort_order else 0, is_active)
        flash('Updated.', 'success')
    return redirect(url_for('admin.config_list'))


@admin_bp.route('/config/<config_type>/<int:item_id>/deactivate', methods=['POST'])
@role_required('Admin')
def config_deactivate(config_type, item_id):
    if config_type not in TABLES:
        flash('Invalid config type.', 'danger')
        return redirect(url_for('admin.config_list'))
    deactivate_item(g.db, config_type, item_id)
    flash('Deactivated.', 'success')
    return redirect(url_for('admin.config_list'))
