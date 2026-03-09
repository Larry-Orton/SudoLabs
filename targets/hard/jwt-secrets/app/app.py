#!/usr/bin/env python3
"""
VaultAPI - Secure Document Vault REST API
==========================================
A deliberately vulnerable Flask application for cybersecurity training.

Vulnerabilities:
  1. Weak JWT signing secret (password123)
  2. Server-Side Template Injection via Jinja2 render_template_string()
  3. SUID python3 binary for privilege escalation
"""

import os
import datetime
import hashlib
import uuid

from flask import (
    Flask, request, jsonify, render_template, render_template_string, redirect
)
import jwt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()

# The intentionally weak JWT secret -- easily crackable via wordlist
JWT_SECRET = "password123"
JWT_ALGORITHM = "HS256"

# ---------------------------------------------------------------------------
# In-memory user store
# ---------------------------------------------------------------------------

users = {}


def _hash_password(password):
    """Simple SHA-256 hash for password storage (intentionally basic)."""
    return hashlib.sha256(password.encode()).hexdigest()


def _seed_users():
    """Pre-seed some default accounts."""
    # Admin with a strong password the attacker cannot guess --
    # forces JWT forgery as the intended path.
    users["admin"] = {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "password": _hash_password("X#9kL!mZ$vQ2wR7pN@4jBcYdA8eF1gHs"),
        "role": "admin",
        "email": "admin@vaultapi.internal",
    }
    # A regular test user for convenience
    users["guest"] = {
        "id": str(uuid.uuid4()),
        "username": "guest",
        "password": _hash_password("guest"),
        "role": "user",
        "email": "guest@vaultapi.internal",
    }


_seed_users()

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _create_token(username, role):
    """Issue a signed JWT with user claims."""
    payload = {
        "user": username,
        "role": role,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token):
    """Decode and verify a JWT. Returns the payload dict or None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _get_token_from_request():
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def _require_auth():
    """Validate the JWT and return the payload, or abort with 401/403."""
    token = _get_token_from_request()
    if not token:
        return None, jsonify({"error": "Missing Authorization header. Use: Bearer <token>"}), 401
    payload = _decode_token(token)
    if not payload:
        return None, jsonify({"error": "Invalid or expired token"}), 403
    return payload, None, None


def _require_admin():
    """Validate the JWT and ensure the role is admin."""
    result = _require_auth()
    payload, err_response, status = result
    if err_response:
        return None, err_response, status
    if payload.get("role") != "admin":
        return None, jsonify({"error": "Admin access required"}), 403
    return payload, None, None


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Landing page with API documentation."""
    return render_template("index.html")


@app.route("/api/docs", methods=["GET"])
def api_docs():
    """Return JSON listing of all API endpoints -- aids reconnaissance."""
    endpoints = [
        {
            "method": "GET",
            "path": "/",
            "description": "API documentation page",
            "auth": False,
        },
        {
            "method": "GET",
            "path": "/api/docs",
            "description": "List all API endpoints (this endpoint)",
            "auth": False,
        },
        {
            "method": "POST",
            "path": "/api/register",
            "description": "Register a new user account",
            "auth": False,
            "body": {"username": "string", "password": "string"},
        },
        {
            "method": "POST",
            "path": "/api/login",
            "description": "Authenticate and receive a JWT",
            "auth": False,
            "body": {"username": "string", "password": "string"},
        },
        {
            "method": "GET",
            "path": "/api/profile",
            "description": "View your user profile",
            "auth": True,
        },
        {
            "method": "GET",
            "path": "/api/vault",
            "description": "List documents in the vault",
            "auth": True,
        },
        {
            "method": "GET",
            "path": "/admin",
            "description": "Admin dashboard (admin role required)",
            "auth": True,
            "note": "Requires role=admin in JWT",
        },
        {
            "method": "POST",
            "path": "/admin/greeting",
            "description": "Set custom admin greeting template",
            "auth": True,
            "note": "Requires role=admin in JWT",
        },
    ]
    return jsonify({
        "application": "VaultAPI",
        "version": "1.4.2",
        "endpoints": endpoints,
    })


# ---------------------------------------------------------------------------
# Authentication routes
# ---------------------------------------------------------------------------


@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user and return a JWT."""
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "JSON body with 'username' and 'password' required"}), 400

    username = data["username"].strip()
    password = data["password"].strip()

    if not username or not password:
        return jsonify({"error": "Username and password must not be empty"}), 400

    if username in users:
        return jsonify({"error": "Username already taken"}), 409

    users[username] = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password": _hash_password(password),
        "role": "user",
        "email": f"{username}@vaultapi.internal",
    }

    token = _create_token(username, "user")
    return jsonify({
        "message": f"User '{username}' registered successfully",
        "token": token,
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT."""
    data = request.get_json(silent=True)
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "JSON body with 'username' and 'password' required"}), 400

    username = data["username"].strip()
    password = data["password"].strip()

    user = users.get(username)
    if not user or user["password"] != _hash_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = _create_token(username, user["role"])
    return jsonify({
        "message": "Login successful",
        "token": token,
    }), 200


# ---------------------------------------------------------------------------
# Authenticated routes
# ---------------------------------------------------------------------------


@app.route("/api/profile", methods=["GET"])
def profile():
    """Return the authenticated user's profile."""
    payload, err_response, status = _require_auth()
    if err_response:
        return err_response, status

    username = payload.get("user", "unknown")
    user = users.get(username, {})

    return jsonify({
        "username": username,
        "role": payload.get("role", "user"),
        "email": user.get("email", "N/A"),
        "id": user.get("id", "N/A"),
        "jwt_claims": payload,
    }), 200


@app.route("/api/vault", methods=["GET"])
def vault():
    """List documents in the vault (mock data)."""
    payload, err_response, status = _require_auth()
    if err_response:
        return err_response, status

    role = payload.get("role", "user")

    documents = [
        {"id": 1, "title": "Q4 Financial Report", "classification": "internal", "owner": "admin"},
        {"id": 2, "title": "Employee Handbook v3", "classification": "public", "owner": "hr"},
        {"id": 3, "title": "Project Roadmap 2024", "classification": "internal", "owner": "admin"},
    ]

    if role == "admin":
        documents.extend([
            {"id": 4, "title": "Security Audit Results", "classification": "confidential", "owner": "admin"},
            {"id": 5, "title": "Incident Response Plan", "classification": "restricted", "owner": "admin"},
            {"id": 6, "title": "Encryption Key Inventory", "classification": "top-secret", "owner": "admin"},
        ])

    return jsonify({
        "vault": "VaultAPI Document Store",
        "user": payload.get("user"),
        "role": role,
        "document_count": len(documents),
        "documents": documents,
    }), 200


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------


@app.route("/admin", methods=["GET"])
def admin_dashboard():
    """Admin dashboard -- requires admin role in JWT."""
    payload, err_response, status = _require_admin()
    if err_response:
        return err_response, status

    username = payload.get("user", "admin")

    # Read the user flag as proof of admin access
    user_flag = ""
    try:
        with open("/home/webapp/user.txt", "r") as f:
            user_flag = f.read().strip()
    except Exception:
        user_flag = "Flag file not found"

    return render_template(
        "admin.html",
        username=username,
        user_flag=user_flag,
        greeting_result=None,
    )


@app.route("/admin/greeting", methods=["POST"])
def admin_greeting():
    """
    Render a custom greeting template.
    ===================================
    VULNERABILITY: Server-Side Template Injection (SSTI)

    The 'template' parameter is passed directly to render_template_string()
    without any sanitization, allowing Jinja2 template injection.

    Benign example:  "Hello {{ username }}, welcome back!"
    Malicious:       "{{ config }}"
    RCE:             "{{ ''.__class__.__mro__[1].__subclasses__() }}"
    """
    payload, err_response, status = _require_admin()
    if err_response:
        return err_response, status

    username = payload.get("user", "admin")
    template_input = request.form.get("template", "")

    if not template_input:
        return redirect("/admin")

    # ------------------------------------------------------------------
    # VULNERABLE: User input rendered directly as a Jinja2 template
    # ------------------------------------------------------------------
    try:
        rendered = render_template_string(template_input, username=username)
    except Exception as e:
        rendered = f"Template Error: {str(e)}"

    # Read user flag again for the admin page context
    user_flag = ""
    try:
        with open("/home/webapp/user.txt", "r") as f:
            user_flag = f.read().strip()
    except Exception:
        user_flag = "Flag file not found"

    return render_template(
        "admin.html",
        username=username,
        user_flag=user_flag,
        greeting_result=rendered,
    )


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "hint": "Try GET /api/docs for available endpoints"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed", "hint": "Check the allowed methods at GET /api/docs"}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  VaultAPI v1.4.2 - Secure Document Vault")
    print("  Listening on http://0.0.0.0:8080")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8080, debug=False)
