"""CorpNet Solutions - Internal API Service.

This API runs on the internal network (172.21.0.2:5000) and is NOT directly
accessible from outside. It exposes sensitive endpoints including one that
leaks administrative credentials in plaintext (CWE-522).
"""

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    """API root - basic info."""
    return jsonify({
        "service": "CorpNet Internal API",
        "version": "2.1.0",
        "status": "running",
        "endpoints": [
            "/api/health",
            "/api/users",
            "/api/credentials",
            "/api/config",
        ],
    })


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "uptime": "47 days, 13:22:08",
        "database": "connected",
        "cache": "connected",
    })


@app.route("/api/credentials")
def credentials():
    """Credential storage endpoint - VULNERABLE: Exposes plaintext credentials (CWE-522).

    This endpoint returns administrative and service account credentials
    with no authentication required. Anyone who can reach the internal
    network can access these credentials.
    """
    return jsonify({
        "warning": "Internal use only - do not expose to DMZ",
        "admin_user": "corpadmin",
        "admin_pass": "C0rpN3t!2024",
        "ssh_user": "deploy",
        "ssh_pass": "d3pl0y_k3y",
        "db_user": "corpdb_admin",
        "db_pass": "db_s3cure_2024",
        "notes": "Admin panel accessible at 172.21.0.3:8443 with admin credentials",
    })


@app.route("/api/users")
def users():
    """Employee directory endpoint."""
    return jsonify({
        "employees": [
            {
                "id": 1,
                "name": "Sarah Chen",
                "role": "CTO",
                "department": "Engineering",
                "email": "s.chen@corpnet.local",
            },
            {
                "id": 2,
                "name": "Marcus Webb",
                "role": "Lead Developer",
                "department": "Engineering",
                "email": "m.webb@corpnet.local",
            },
            {
                "id": 3,
                "name": "Elena Rodriguez",
                "role": "System Administrator",
                "department": "IT Operations",
                "email": "e.rodriguez@corpnet.local",
            },
            {
                "id": 4,
                "name": "James Park",
                "role": "Security Analyst",
                "department": "InfoSec",
                "email": "j.park@corpnet.local",
            },
            {
                "id": 5,
                "name": "Deploy Service Account",
                "role": "Automated Deployment",
                "department": "DevOps",
                "email": "deploy@corpnet.local",
            },
        ]
    })


@app.route("/api/config")
def config():
    """Internal network configuration endpoint."""
    return jsonify({
        "network": {
            "dmz_subnet": "172.20.0.0/24",
            "internal_subnet": "172.21.0.0/24",
            "gateway": "172.21.0.1",
        },
        "services": {
            "internal_api": {
                "host": "172.21.0.2",
                "port": 5000,
                "protocol": "http",
            },
            "admin_panel": {
                "host": "172.21.0.3",
                "port": 8443,
                "protocol": "http",
                "auth": "basic",
                "note": "Use corporate admin credentials",
            },
            "webapp_internal": {
                "host": "172.21.0.4",
                "port": 8080,
                "protocol": "http",
                "note": "DMZ webapp internal interface",
            },
        },
        "dns": {
            "api.corpnet.local": "172.21.0.2",
            "admin.corpnet.local": "172.21.0.3",
            "www.corpnet.local": "172.21.0.4",
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
