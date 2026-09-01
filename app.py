import os
import sys
from datetime import date
from flask import Flask, g

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from models.db import init_db, query_db
from routes.auth import auth_bp
from routes.actions import actions_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp
from routes.reports import reports_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(actions_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reports_bp)

    @app.context_processor
    def inject_globals():
        today = date.today().isoformat()
        reminders = []
        if hasattr(g, 'user') and g.user:
            db = g.db
            overdue = query_db(db, """
                SELECT COUNT(*) AS n FROM actions a
                JOIN config_statuses s ON a.status_id = s.id
                WHERE a.due_date < ? AND s.name NOT IN ('Completed','Closed')
                AND (a.owner_id = ? OR a.exec_sponsor_id = ?)
            """, (today, g.user['id'], g.user['id']), one=True)
            if overdue and overdue['n'] > 0:
                reminders.append(f"You have {overdue['n']} overdue action(s).")

            due_soon = query_db(db, """
                SELECT COUNT(*) AS n FROM actions a
                JOIN config_statuses s ON a.status_id = s.id
                WHERE a.due_date BETWEEN ? AND date(?, '+7 days')
                AND s.name NOT IN ('Completed','Closed')
                AND (a.owner_id = ? OR a.exec_sponsor_id = ?)
            """, (today, today, g.user['id'], g.user['id']), one=True)
            if due_soon and due_soon['n'] > 0:
                reminders.append(f"{due_soon['n']} action(s) due within 7 days.")

        return {'today': today, 'reminders': reminders}

    with app.app_context():
        init_db()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=config.DEBUG, port=5000)
