"""Database initialization for Nexus Corp Employee Portal.

Creates the SQLite database with users, employees, and secrets tables.
This script is run as a post_start command by the Howl engine.
"""

import os
import sqlite3

DATABASE = "/app/data/nexuscorp.db"


def initialize():
    """Create and populate the database."""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # ------------------------------------------------------------------
    # Users table - stores login credentials
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert default users
    users = [
        ("admin", "N3xus$ecureP@ss2024!", "admin", "admin@nexuscorp.internal"),
        ("jsmith", "password123", "employee", "jsmith@nexuscorp.internal"),
        ("mwilliams", "Welcome1!", "employee", "mwilliams@nexuscorp.internal"),
        ("tjohnson", "Summer2024", "manager", "tjohnson@nexuscorp.internal"),
        ("agarcia", "nexus4life", "employee", "agarcia@nexuscorp.internal"),
        ("svc_backup", "b@ckup_2024_auto", "service", "svc_backup@nexuscorp.internal"),
    ]

    for user in users:
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role, email) "
                "VALUES (?, ?, ?, ?)",
                user,
            )
        except sqlite3.IntegrityError:
            pass  # User already exists

    # ------------------------------------------------------------------
    # Employees table - used by the search page
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            hire_date TEXT
        )
    """)

    employees = [
        ("Alice Chen", "Engineering", "achen@nexuscorp.internal", "555-0101", "2021-03-15"),
        ("Bob Martinez", "Engineering", "bmartinez@nexuscorp.internal", "555-0102", "2020-08-22"),
        ("Carol Davis", "Human Resources", "cdavis@nexuscorp.internal", "555-0201", "2019-01-10"),
        ("David Kim", "Finance", "dkim@nexuscorp.internal", "555-0301", "2022-06-01"),
        ("Eve Thompson", "Security", "ethompson@nexuscorp.internal", "555-0401", "2020-11-30"),
        ("Frank Wilson", "Engineering", "fwilson@nexuscorp.internal", "555-0103", "2023-02-14"),
        ("Grace Liu", "Marketing", "gliu@nexuscorp.internal", "555-0501", "2021-09-05"),
        ("Henry Brown", "Operations", "hbrown@nexuscorp.internal", "555-0601", "2018-04-20"),
        ("Irene Patel", "Engineering", "ipatel@nexuscorp.internal", "555-0104", "2022-12-01"),
        ("James Robinson", "Finance", "jrobinson@nexuscorp.internal", "555-0302", "2021-07-18"),
    ]

    for emp in employees:
        try:
            cursor.execute(
                "INSERT INTO employees (name, department, email, phone, hire_date) "
                "VALUES (?, ?, ?, ?, ?)",
                emp,
            )
        except sqlite3.IntegrityError:
            pass

    # ------------------------------------------------------------------
    # Secrets table - the target for UNION-based extraction
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secret_key TEXT NOT NULL,
            secret_value TEXT NOT NULL,
            description TEXT
        )
    """)

    # Read the db_flag from disk to store in the secrets table
    db_flag = "HOWL{placeholder_db_flag}"
    try:
        with open("/opt/secrets/db_flag.txt", "r") as f:
            db_flag = f.read().strip()
    except (FileNotFoundError, PermissionError):
        pass

    secrets = [
        ("api_master_key", "NXC-4f8a-9b2e-7d1c-3e6f", "Master API key for internal services"),
        ("database_root_pass", "r00t_db_N3xus!", "Root database password"),
        ("aws_access_key", "AKIA3EXAMPLE7NEXUS", "AWS access key for S3 backups"),
        ("jwt_signing_secret", "h5Kz9$mPqR2wXvN8", "JWT token signing secret"),
        ("flag", db_flag, "Classified operational flag -- DO NOT SHARE"),
        ("vpn_preshared_key", "NexusVPN-Pr3$hared-2024", "Corporate VPN pre-shared key"),
        ("smtp_relay_password", "m@ilR3lay_Nxs!", "SMTP relay authentication"),
    ]

    for secret in secrets:
        try:
            cursor.execute(
                "INSERT INTO secrets (secret_key, secret_value, description) "
                "VALUES (?, ?, ?)",
                secret,
            )
        except sqlite3.IntegrityError:
            pass

    # ------------------------------------------------------------------
    # Audit log table (adds realism, not used in attacks)
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL,
            username TEXT,
            ip_address TEXT,
            details TEXT
        )
    """)

    sample_logs = [
        ("LOGIN_SUCCESS", "admin", "10.0.0.1", "Admin login from management VLAN"),
        ("LOGIN_SUCCESS", "jsmith", "192.168.1.45", "Regular login"),
        ("LOGIN_FAILED", "admin", "203.0.113.50", "Failed login attempt - wrong password"),
        ("PASSWORD_CHANGE", "mwilliams", "192.168.1.102", "Password reset completed"),
        ("DATA_EXPORT", "tjohnson", "192.168.1.88", "Exported Q3 financial report"),
        ("LOGIN_FAILED", "root", "203.0.113.50", "Failed login - user does not exist"),
        ("SEARCH_QUERY", "agarcia", "192.168.1.67", "Searched for: Engineering team"),
    ]

    for log_entry in sample_logs:
        cursor.execute(
            "INSERT INTO audit_log (action, username, ip_address, details) "
            "VALUES (?, ?, ?, ?)",
            log_entry,
        )

    conn.commit()
    conn.close()
    print("[init_db] Database initialized successfully at", DATABASE)


if __name__ == "__main__":
    initialize()
