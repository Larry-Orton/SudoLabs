"""Nexus Corp Employee Portal - Vulnerable Flask Application.

WARNING: This application is intentionally vulnerable to SQL injection.
         It is designed for cybersecurity training purposes only.
         DO NOT deploy this in any production environment.
"""

import os
import sqlite3

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = "nexuscorp-internal-secret-key-2024"

DATABASE = "/app/data/nexuscorp.db"


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------
# Static file route for /var/www/html (recon discovery target)
# ---------------------------------------------------------------
@app.route("/static-assets/<path:filename>")
def serve_static_html(filename):
    return send_from_directory("/var/www/html", filename)


@app.route("/.hidden/<path:filename>")
def serve_hidden(filename):
    """Serve files from the hidden directory -- recon flag lives here."""
    return send_from_directory("/var/www/html/.hidden", filename)


# ---------------------------------------------------------------
# Index - redirects to login
# ---------------------------------------------------------------
@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ---------------------------------------------------------------
# LOGIN - Vulnerable to SQL Injection (CWE-89)
# ---------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # VULNERABLE: Direct string concatenation in SQL query
        # This allows authentication bypass via SQL injection.
        # Example payload: admin' OR '1'='1' --
        query = (
            "SELECT * FROM users WHERE username = '"
            + username
            + "' AND password = '"
            + password
            + "'"
        )

        try:
            db = get_db()
            result = db.execute(query).fetchone()
            db.close()

            if result:
                session["logged_in"] = True
                session["username"] = result["username"]
                session["role"] = result["role"]

                # Read user flag for display on dashboard
                user_flag_path = "/home/webapp/user.txt"
                user_flag = ""
                try:
                    with open(user_flag_path, "r") as f:
                        user_flag = f.read().strip()
                except (FileNotFoundError, PermissionError):
                    user_flag = "[flag file not accessible]"

                session["user_flag"] = user_flag
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid credentials. Access denied."
        except sqlite3.Error as e:
            error = f"Database error: {e}"

    return render_template("login.html", error=error)


# ---------------------------------------------------------------
# DASHBOARD - Requires authentication
# ---------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session.get("username", "Unknown"),
        role=session.get("role", "employee"),
        user_flag=session.get("user_flag", ""),
    )


# ---------------------------------------------------------------
# SEARCH - Vulnerable to UNION-based SQL Injection
# ---------------------------------------------------------------
@app.route("/search", methods=["GET", "POST"])
def search():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    results = []
    search_query = ""
    error = None

    if request.method == "POST":
        search_query = request.form.get("query", "")

        # VULNERABLE: Direct string concatenation allowing UNION injection
        # The query returns 3 columns: name, department, email
        # Attacker can use:
        #   ' UNION SELECT sql,2,3 FROM sqlite_master --
        #   ' UNION SELECT secret_key,secret_value,description FROM secrets --
        query = (
            "SELECT name, department, email FROM employees "
            "WHERE name LIKE '%" + search_query + "%' "
            "OR department LIKE '%" + search_query + "%'"
        )

        try:
            db = get_db()
            cursor = db.execute(query)
            results = cursor.fetchall()
            db.close()
        except sqlite3.Error as e:
            error = f"Search error: {e}"

    return render_template(
        "search.html",
        results=results,
        query=search_query,
        error=error,
    )


# ---------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------
# robots.txt - gives a hint about hidden directories
# ---------------------------------------------------------------
@app.route("/robots.txt")
def robots():
    content = (
        "User-agent: *\n"
        "Disallow: /.hidden/\n"
        "Disallow: /admin/\n"
        "Disallow: /backup/\n"
    )
    return content, 200, {"Content-Type": "text/plain"}


# ---------------------------------------------------------------
# Sitemap hint
# ---------------------------------------------------------------
@app.route("/admin")
def admin_redirect():
    return "403 Forbidden - Admin panel relocated.", 403


@app.route("/backup")
def backup_redirect():
    return "403 Forbidden - Backup directory restricted.", 403


if __name__ == "__main__":
    # Initialize database if it doesn't exist
    if not os.path.exists(DATABASE):
        import init_db
        init_db.initialize()

    app.run(host="0.0.0.0", port=8080, debug=False)
