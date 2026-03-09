"""CorpNet Solutions - Admin Panel Service.

This admin panel runs on the internal network (172.21.0.3:8443) and requires
HTTP Basic Auth. It contains a diagnostics feature that passes user input
directly to os.popen() (CWE-78: OS Command Injection).
"""

import os
from functools import wraps

from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

# Admin credentials - these match what the internal API leaks
ADMIN_USER = "corpadmin"
ADMIN_PASS = "C0rpN3t!2024"


def check_auth(username, password):
    """Verify admin credentials."""
    return username == ADMIN_USER and password == ADMIN_PASS


def authenticate():
    """Send a 401 response to trigger Basic Auth prompt."""
    return Response(
        "Authentication required. Please provide valid admin credentials.\n",
        401,
        {"WWW-Authenticate": 'Basic realm="CorpNet Admin Panel"'},
    )


def requires_auth(f):
    """Decorator for endpoints that require Basic Auth."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    """Redirect to admin dashboard."""
    return '<html><body><p>CorpNet Admin Panel. <a href="/admin">Login</a></p></body></html>'


@app.route("/admin")
@requires_auth
def admin_dashboard():
    """Admin dashboard - main page."""
    return render_template("admin.html")


@app.route("/admin/diag", methods=["GET", "POST"])
@requires_auth
def diagnostics():
    """Diagnostics endpoint - VULNERABLE to OS Command Injection (CWE-78).

    The 'cmd' parameter is passed directly to os.popen() with no
    sanitization. Intended for ping and nslookup but an attacker can
    inject arbitrary commands.
    """
    output = None
    cmd = ""

    if request.method == "POST":
        cmd = request.form.get("cmd", "").strip()
        if cmd:
            # VULNERABLE: User input passed directly to os.popen()
            # An attacker can inject arbitrary commands (e.g., ; cat /etc/passwd)
            try:
                output = os.popen(cmd).read()
            except Exception as e:
                output = f"Error executing command: {str(e)}"
        else:
            output = "Please enter a diagnostic command."
    elif request.method == "GET" and request.args.get("cmd"):
        # Also accept GET requests with cmd parameter for easy SSRF chaining
        cmd = request.args.get("cmd", "").strip()
        if cmd:
            try:
                output = os.popen(cmd).read()
            except Exception as e:
                output = f"Error executing command: {str(e)}"

    return render_template("admin.html", diag_output=output, diag_cmd=cmd, active_page="diag")


@app.route("/admin/users")
@requires_auth
def user_management():
    """User management page."""
    users = [
        {"username": "corpadmin", "role": "Administrator", "status": "Active", "last_login": "2024-03-15 09:22:11"},
        {"username": "deploy", "role": "Service Account", "status": "Active", "last_login": "2024-03-15 08:00:00"},
        {"username": "s.chen", "role": "CTO", "status": "Active", "last_login": "2024-03-14 17:45:33"},
        {"username": "m.webb", "role": "Developer", "status": "Active", "last_login": "2024-03-15 10:12:07"},
        {"username": "e.rodriguez", "role": "SysAdmin", "status": "Active", "last_login": "2024-03-15 07:30:00"},
    ]
    return render_template("admin.html", users=users, active_page="users")


@app.route("/admin/status")
@requires_auth
def system_status():
    """System status API endpoint."""
    return jsonify({
        "admin_panel": "running",
        "version": "1.4.2",
        "network": {
            "internal_api": "172.21.0.2:5000",
            "admin_panel": "172.21.0.3:8443",
            "webapp_internal": "172.21.0.4:8080",
        },
        "uptime": "47 days",
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8443, debug=False)
