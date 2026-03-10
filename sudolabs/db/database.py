"""SQLite database connection manager for SudoLabs."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from sudolabs.config import DB_FILE, ensure_sudolabs_home


SCHEMA_FILE = Path(__file__).parent / "schema.sql"

# Current schema version — bump this when adding migrations.
SCHEMA_VERSION = 2

# ---------------------------------------------------------------------------
# Migration functions
# ---------------------------------------------------------------------------

def _migrate_v2(conn: sqlite3.Connection):
    """Add category column to target_progress table."""
    # Check if column already exists (safe for re-runs)
    cursor = conn.execute("PRAGMA table_info(target_progress)")
    columns = [row[1] for row in cursor.fetchall()]
    if "category" not in columns:
        conn.execute(
            "ALTER TABLE target_progress ADD COLUMN category TEXT NOT NULL DEFAULT ''"
        )


# Ordered list of migration functions.  Each entry is (version, callable).
# A migration runs when the DB is at a version lower than the entry's version.
# Migrations receive a sqlite3.Connection and must NOT commit (caller does).
_MIGRATIONS: list[tuple[int, callable]] = [
    (2, _migrate_v2),
]


def _get_schema_version(conn: sqlite3.Connection) -> int:
    """Return the current schema version stored in the DB (0 if unset)."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "  id INTEGER PRIMARY KEY CHECK (id = 1),"
        "  version INTEGER NOT NULL DEFAULT 1"
        ")"
    )
    row = conn.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
    if row is None:
        conn.execute("INSERT INTO schema_version (id, version) VALUES (1, ?)", (SCHEMA_VERSION,))
        return SCHEMA_VERSION
    return row[0]


def _set_schema_version(conn: sqlite3.Connection, version: int):
    conn.execute("UPDATE schema_version SET version = ? WHERE id = 1", (version,))


def _run_migrations(conn: sqlite3.Connection):
    """Apply any pending schema migrations in order."""
    current = _get_schema_version(conn)
    for target_ver, migrate_fn in _MIGRATIONS:
        if current < target_ver:
            migrate_fn(conn)
            _set_schema_version(conn, target_ver)
            current = target_ver
    conn.commit()


def init_db():
    """Initialize the database with the schema and run any pending migrations."""
    ensure_sudolabs_home()
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row

    with open(SCHEMA_FILE, "r") as f:
        conn.executescript(f.read())

    # Run schema migrations for existing databases
    _run_migrations(conn)

    # Ensure a default profile exists
    cursor = conn.execute("SELECT COUNT(*) FROM profile")
    if cursor.fetchone()[0] == 0:
        conn.execute("INSERT INTO profile (username) VALUES ('hunter')")
        conn.commit()

    conn.close()


@contextmanager
def get_db():
    """Context manager yielding a database connection."""
    ensure_sudolabs_home()

    if not DB_FILE.exists():
        init_db()

    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
