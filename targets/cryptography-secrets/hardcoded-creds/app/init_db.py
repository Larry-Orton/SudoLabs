"""Initialize the MySQL database with sample data."""

import mysql.connector
import time


def initialize():
    """Wait for MySQL and create initial data."""
    # Wait for MySQL to be ready
    for attempt in range(30):
        try:
            conn = mysql.connector.connect(
                host="mysql",
                port=3306,
                user="inventory_admin",
                password="V@ntage_S3cret!2024",
                database="inventory",
            )
            break
        except mysql.connector.Error:
            time.sleep(2)
    else:
        print("Could not connect to MySQL after 30 attempts")
        return

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL,
            role VARCHAR(50) DEFAULT 'employee'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            sku VARCHAR(50) NOT NULL,
            quantity INT DEFAULT 0,
            location VARCHAR(100)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            secret_key VARCHAR(200) NOT NULL,
            secret_value TEXT NOT NULL,
            description VARCHAR(500)
        )
    """)

    # Insert users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            [
                ("admin", "Adm1n_M@ster!99", "admin"),
                ("jsmith", "password123", "employee"),
                ("analyst", "report2024", "viewer"),
            ],
        )

    # Insert inventory items
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO inventory (name, sku, quantity, location) VALUES (%s, %s, %s, %s)",
            [
                ("Server Rack Unit", "SRU-4420", 12, "Warehouse A"),
                ("Network Switch 48P", "NSW-4800", 8, "Warehouse B"),
                ("UPS Battery Pack", "UPS-2200", 25, "Storage C"),
                ("Fiber Patch Cable", "FPC-1005", 200, "Storage A"),
                ("Firewall Appliance", "FWA-9100", 3, "Secure Room"),
            ],
        )

    # Insert the flag into secrets table
    cursor.execute("SELECT COUNT(*) FROM secrets")
    if cursor.fetchone()[0] == 0:
        # Read the root flag
        try:
            with open("/root/root.txt", "r") as f:
                root_flag = f.read().strip()
        except Exception:
            root_flag = "SUDO{placeholder_root_flag}"

        cursor.executemany(
            "INSERT INTO secrets (secret_key, secret_value, description) VALUES (%s, %s, %s)",
            [
                ("api_key", "sk-vantage-prod-88a3f2c1d4e5", "Production API key"),
                ("root_flag", root_flag, "System root flag"),
                ("backup_key", "AES256-vault-key-2024-prod", "Backup encryption key"),
            ],
        )

    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    initialize()
