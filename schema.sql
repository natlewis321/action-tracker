-- Users & Auth
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('Admin','Exec','Owner','Viewer')),
    department      TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at      TEXT NOT NULL
);

-- Configuration (admin-editable picklists)
CREATE TABLE IF NOT EXISTS config_categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS config_statuses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS config_committees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS config_departments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    is_active       INTEGER NOT NULL DEFAULT 1
);

-- Actions (core entity)
CREATE TABLE IF NOT EXISTS actions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    description     TEXT,
    category_id     INTEGER NOT NULL REFERENCES config_categories(id),
    source_committee_id INTEGER REFERENCES config_committees(id),
    reporting_committee_id INTEGER REFERENCES config_committees(id),
    department_id   INTEGER REFERENCES config_departments(id),
    date_raised     TEXT NOT NULL,
    due_date        TEXT,
    priority        TEXT NOT NULL CHECK (priority IN ('Critical','High','Medium','Low'))
                        DEFAULT 'Medium',
    status_id       INTEGER NOT NULL REFERENCES config_statuses(id),
    owner_id        INTEGER REFERENCES users(id),
    exec_sponsor_id INTEGER REFERENCES users(id),
    closure_evidence TEXT,
    closed_by_id    INTEGER REFERENCES users(id),
    closed_at       TEXT,
    created_by_id   INTEGER NOT NULL REFERENCES users(id),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Comments / update thread
CREATE TABLE IF NOT EXISTS action_comments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id       INTEGER NOT NULL REFERENCES actions(id),
    user_id         INTEGER NOT NULL REFERENCES users(id),
    body            TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Full audit trail
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id       INTEGER NOT NULL REFERENCES actions(id),
    user_id         INTEGER NOT NULL REFERENCES users(id),
    field_name      TEXT NOT NULL,
    old_value       TEXT,
    new_value       TEXT,
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status_id);
CREATE INDEX IF NOT EXISTS idx_actions_owner ON actions(owner_id);
CREATE INDEX IF NOT EXISTS idx_actions_exec ON actions(exec_sponsor_id);
CREATE INDEX IF NOT EXISTS idx_actions_due ON actions(due_date);
CREATE INDEX IF NOT EXISTS idx_actions_category ON actions(category_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action_id);
CREATE INDEX IF NOT EXISTS idx_comments_action ON action_comments(action_id);
