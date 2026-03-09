"""LinkLens - Corporate URL Preview Tool (Vulnerable to SSRF / CWE-918).

This application runs two Flask servers:
  1. Main web app on port 8080 - public-facing URL preview tool
  2. Internal API on port 5000 - localhost-only service with sensitive config

The main app fetches arbitrary URLs without validation, enabling SSRF.
The internal API exposes admin credentials at /api/config without auth.
The admin panel has a status check feature vulnerable to command injection.
"""

import json
import os
import subprocess
import threading
from functools import wraps

import requests
from flask import Flask, Response, render_template, request, session

# =============================================================================
# Internal API Service (port 5000 - localhost only)
# =============================================================================

internal_app = Flask("internal_api")

# Simulated internal configuration with leaked credentials
INTERNAL_CONFIG = {
    "app_name": "LinkLens",
    "version": "2.3.1",
    "admin_user": "admin",
    "admin_pass": "Sup3rS3cret!",
    "db_host": "localhost",
    "db_port": 5432,
    "db_name": "linklens_prod",
    "secret_key": "d7a9f3e2b1c4058697adef1234567890",
    "internal_note": "DO NOT expose this service externally",
}

INTERNAL_USERS = [
    {"id": 1, "username": "admin", "role": "administrator", "email": "admin@linklens.corp"},
    {"id": 2, "username": "jdoe", "role": "editor", "email": "jdoe@linklens.corp"},
    {"id": 3, "username": "msmith", "role": "viewer", "email": "msmith@linklens.corp"},
    {"id": 4, "username": "svc-backup", "role": "service", "email": "backup@linklens.corp"},
]


@internal_app.route("/")
def internal_index():
    """Internal API root."""
    return json.dumps({
        "service": "LinkLens Internal API",
        "version": "1.0.0",
        "endpoints": ["/api/health", "/api/config", "/api/users"],
        "warning": "This service should only be accessible from localhost",
    }), 200, {"Content-Type": "application/json"}


@internal_app.route("/api/health")
def internal_health():
    """Health check endpoint."""
    return json.dumps({"status": "ok", "uptime": "14d 6h 32m"}), 200, {
        "Content-Type": "application/json"
    }


@internal_app.route("/api/config")
def internal_config():
    """Configuration endpoint - VULNERABLE: leaks admin credentials."""
    return json.dumps(INTERNAL_CONFIG, indent=2), 200, {
        "Content-Type": "application/json"
    }


@internal_app.route("/api/users")
def internal_users():
    """User listing endpoint."""
    return json.dumps({"users": INTERNAL_USERS}, indent=2), 200, {
        "Content-Type": "application/json"
    }


def run_internal_api():
    """Start the internal API server in a background thread."""
    internal_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


# =============================================================================
# Main Web Application (port 8080 - public facing)
# =============================================================================

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Admin credentials (in a real scenario these would come from the internal API)
ADMIN_USER = "admin"
ADMIN_PASS = "Sup3rS3cret!"


def check_auth(username, password):
    """Verify admin credentials."""
    return username == ADMIN_USER and password == ADMIN_PASS


def requires_auth(f):
    """Decorator for routes that require basic authentication."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Access Denied. Valid credentials required.\n",
                401,
                {"WWW-Authenticate": 'Basic realm="LinkLens Admin"'},
            )
        return f(*args, **kwargs)

    return decorated


@app.route("/")
def index():
    """Landing page with URL preview form."""
    return render_template("index.html")


@app.route("/preview", methods=["POST"])
def preview():
    """URL preview endpoint - VULNERABLE to SSRF (CWE-918).

    Fetches any user-supplied URL server-side with no validation,
    allowlisting, or blocklisting. An attacker can use this to:
    - Access internal services (127.0.0.1, localhost, internal IPs)
    - Scan internal network ports
    - Read cloud metadata endpoints
    - Exfiltrate data from internal systems
    """
    url = request.form.get("url", "").strip()

    if not url:
        return render_template("index.html", error="Please enter a URL to preview.")

    # VULNERABLE: No URL validation - fetches anything the user provides
    try:
        resp = requests.get(url, timeout=5, allow_redirects=True)
        content = resp.text
        status_code = resp.status_code
        content_type = resp.headers.get("Content-Type", "unknown")

        return render_template(
            "index.html",
            preview_content=content,
            preview_url=url,
            preview_status=status_code,
            preview_type=content_type,
        )
    except requests.exceptions.ConnectionError:
        return render_template(
            "index.html",
            error=f"Connection failed: Could not connect to {url}",
        )
    except requests.exceptions.Timeout:
        return render_template(
            "index.html",
            error=f"Request timed out while fetching {url}",
        )
    except requests.exceptions.MissingSchema:
        return render_template(
            "index.html",
            error="Invalid URL. Please include the protocol (e.g., http:// or https://).",
        )
    except Exception as e:
        return render_template(
            "index.html",
            error=f"Error fetching URL: {str(e)}",
        )


@app.route("/admin")
@requires_auth
def admin_dashboard():
    """Admin dashboard - requires authentication."""
    return render_template("admin.html")


@app.route("/admin/status")
@requires_auth
def admin_status():
    """Server status check - VULNERABLE to command injection.

    The 'host' parameter is passed directly into a subprocess call
    without any sanitization, allowing command injection via shell
    metacharacters such as ; | && ` $()
    """
    host = request.args.get("host", "").strip()

    if not host:
        return render_template("admin.html", status_error="Please enter a host to check.")

    # VULNERABLE: User input passed directly to shell command
    try:
        result = subprocess.run(
            f"ping -c 2 -W 2 {host}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = "Error: Status check timed out."
    except Exception as e:
        output = f"Error: {str(e)}"

    return render_template("admin.html", status_output=output, status_host=host)


@app.route("/robots.txt")
def robots():
    """Robots.txt - leaks the existence of /admin."""
    return Response(
        "User-agent: *\nDisallow: /admin\nDisallow: /preview\n",
        mimetype="text/plain",
    )


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    # Start the internal API service in a background thread
    internal_thread = threading.Thread(target=run_internal_api, daemon=True)
    internal_thread.start()
    print("[*] Internal API started on 127.0.0.1:5000")

    # Start the main web application
    print("[*] LinkLens web app starting on 0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)
