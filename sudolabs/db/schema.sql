-- Howl Database Schema

CREATE TABLE IF NOT EXISTS profile (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL DEFAULT 'hunter',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    total_score INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS target_progress (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    target_slug     TEXT NOT NULL UNIQUE,
    difficulty      TEXT NOT NULL,
    category        TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'not_started',
    best_score      INTEGER NOT NULL DEFAULT 0,
    best_time_secs  INTEGER,
    attempts        INTEGER NOT NULL DEFAULT 0,
    first_started   TEXT,
    completed_at    TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT NOT NULL UNIQUE,
    target_slug       TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'active',
    started_at        TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at      TEXT,
    current_stage     INTEGER NOT NULL DEFAULT 0,
    total_score       INTEGER NOT NULL DEFAULT 0,
    time_elapsed_secs INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS stage_completions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    stage_index     INTEGER NOT NULL,
    stage_name      TEXT NOT NULL,
    flag_submitted  TEXT NOT NULL,
    points_earned   INTEGER NOT NULL DEFAULT 0,
    hints_used_l1   INTEGER NOT NULL DEFAULT 0,
    hints_used_l2   INTEGER NOT NULL DEFAULT 0,
    hints_used_l3   INTEGER NOT NULL DEFAULT 0,
    hint_multiplier REAL NOT NULL DEFAULT 1.0,
    time_bonus      REAL NOT NULL DEFAULT 1.0,
    completed_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    UNIQUE(session_id, stage_index)
);

CREATE TABLE IF NOT EXISTS hint_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    stage_index     INTEGER NOT NULL,
    hint_level      INTEGER NOT NULL,
    hint_source     TEXT NOT NULL DEFAULT 'static',
    requested_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    achievement_id  TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    description     TEXT NOT NULL,
    points          INTEGER NOT NULL DEFAULT 0,
    unlocked_at     TEXT NOT NULL DEFAULT (datetime('now')),
    trigger_session TEXT,
    trigger_target  TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_target ON sessions(target_slug);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_stage_completions_session ON stage_completions(session_id);
CREATE INDEX IF NOT EXISTS idx_hint_log_session ON hint_log(session_id);
