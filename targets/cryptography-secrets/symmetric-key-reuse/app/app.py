"""NovaBridge Systems - Dual Service Application.

WARNING: This application is intentionally vulnerable (CWE-327).
         Two services share the same AES encryption key.
         DO NOT deploy this in any production environment.
"""

import json
import os
import threading

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from flask import Flask, jsonify, render_template_string, request, send_from_directory

# ==================================================================
# VULNERABILITY: Shared AES key across both services (CWE-327)
# ==================================================================
SHARED_AES_KEY = b"NovaBr1dge_K3y!!"  # 16 bytes = AES-128


def encrypt_data(plaintext):
    """Encrypt data with AES-CBC using the shared key."""
    cipher = AES.new(SHARED_AES_KEY, AES.MODE_CBC)
    ct = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    # Return IV + ciphertext as hex
    return (cipher.iv + ct).hex()


def decrypt_data(hex_data):
    """Decrypt AES-CBC data using the shared key."""
    raw = bytes.fromhex(hex_data)
    iv = raw[:16]
    ct = raw[16:]
    cipher = AES.new(SHARED_AES_KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size).decode()


# Pre-encrypt some vault secrets
def build_vault():
    """Build the encrypted vault data."""
    root_flag = "SUDO{placeholder_root_flag}"
    try:
        with open("/root/root.txt") as f:
            root_flag = f.read().strip()
    except Exception:
        pass

    secrets = {
        "db_credentials": encrypt_data("user=novadb_admin password=N0va_DB!2024 host=db.internal"),
        "api_master_key": encrypt_data("api-key-nova-master-9f8e7d6c5b4a3210"),
        "root_flag": encrypt_data(root_flag),
        "ssh_key_passphrase": encrypt_data("N0vaBr1dge_SSH_P@ss!"),
        "admin_password": encrypt_data("Adm1n_N0va!2024"),
    }
    return secrets


# ======================================================================
# SERVICE A: Credentials Vault (port 8080)
# ======================================================================
vault_app = Flask("vault")
vault_app.secret_key = "vault-internal-key"

VAULT_INDEX = """
<!DOCTYPE html>
<html>
<head><title>NovaBridge Credentials Vault</title>
<style>
body { font-family: 'Consolas', monospace; margin: 0; background: #0c0c1d; color: #a0a0c0; }
.header { background: #1a1a3e; padding: 20px 40px; border-bottom: 2px solid #3d3d8e; }
.header h1 { color: #7878ff; margin: 0; }
.container { max-width: 800px; margin: 30px auto; padding: 20px; }
.card { background: #1a1a3e; padding: 20px; border-radius: 6px; border: 1px solid #3d3d8e; margin: 15px 0; }
code { background: #0c0c1d; padding: 2px 6px; border-radius: 3px; color: #78ff78; }
a { color: #7878ff; }
</style>
</head>
<body>
<div class="header"><h1>NovaBridge Credentials Vault</h1><p>Secure Encrypted Storage</p></div>
<div class="container">
    <div class="card">
        <h3>API Endpoints</h3>
        <ul>
            <li><code>GET /api/vault/secrets</code> - List encrypted secrets</li>
            <li><code>GET /api/vault/info</code> - Vault information</li>
        </ul>
    </div>
    <div class="card">
        <p>All credentials are stored using AES-256-CBC encryption.</p>
        <p>Encryption Algorithm: AES-CBC | Key Size: 128-bit | Format: hex(IV + ciphertext)</p>
    </div>
</div>
</body>
</html>
"""


@vault_app.route("/")
def vault_index():
    return render_template_string(VAULT_INDEX)


@vault_app.route("/api/vault/secrets")
def vault_secrets():
    vault_data = build_vault()
    vault_flag = "[not accessible]"
    try:
        with open("/opt/novabridge/vault_flag.txt") as f:
            vault_flag = f.read().strip()
    except Exception:
        pass

    return jsonify({
        "vault": "NovaBridge Credentials Vault",
        "encryption": "AES-128-CBC",
        "format": "hex(IV_16bytes + ciphertext)",
        "vault_flag": vault_flag,
        "secrets": vault_data,
    })


@vault_app.route("/api/vault/info")
def vault_info():
    return jsonify({
        "service": "NovaBridge Vault",
        "version": "2.3.1",
        "encryption": "AES-CBC",
        "key_size": 128,
        "entries": 5,
        "status": "locked",
        "note": "Decryption key managed by config-service on port 3000",
    })


@vault_app.route("/.ops/<path:filename>")
def vault_serve_ops(filename):
    return send_from_directory("/var/www/html/.ops", filename)


@vault_app.route("/robots.txt")
def vault_robots():
    return "User-agent: *\nDisallow: /api/\nDisallow: /.ops/\n", 200, {"Content-Type": "text/plain"}


# ======================================================================
# SERVICE B: Configuration Service (port 3000)
# ======================================================================
config_app = Flask("config")
config_app.secret_key = "config-internal-key"

CONFIG_INDEX = """
<!DOCTYPE html>
<html>
<head><title>NovaBridge Config Service</title>
<style>
body { font-family: 'Consolas', monospace; margin: 0; background: #0d1117; color: #c9d1d9; }
.header { background: #161b22; padding: 20px 40px; border-bottom: 1px solid #30363d; }
.header h1 { color: #58a6ff; margin: 0; }
.container { max-width: 800px; margin: 30px auto; padding: 20px; }
.card { background: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; margin: 15px 0; }
a { color: #58a6ff; }
code { background: #0d1117; padding: 2px 6px; border-radius: 3px; color: #7ee787; }
</style>
</head>
<body>
<div class="header"><h1>NovaBridge Config Service</h1><p>Internal Configuration API</p></div>
<div class="container">
    <div class="card">
        <h3>API Endpoints</h3>
        <ul>
            <li><code>GET /api/config/services</code> - List configured services</li>
            <li><code>GET /api/config/health</code> - Service health check</li>
        </ul>
    </div>
</div>
</body>
</html>
"""


@config_app.route("/")
def config_index():
    return render_template_string(CONFIG_INDEX)


@config_app.route("/api/config/services")
def config_services():
    return jsonify({
        "services": [
            {"name": "vault", "port": 8080, "status": "running"},
            {"name": "config-service", "port": 3000, "status": "running"},
            {"name": "database", "port": 5432, "status": "running"},
        ]
    })


@config_app.route("/api/config/health")
def config_health():
    return jsonify({"status": "healthy", "version": "1.8.0"})


# ------------------------------------------------------------------
# VULNERABILITY: Debug endpoint exposes the shared encryption key
# ------------------------------------------------------------------
@config_app.route("/debug/config")
def debug_config():
    """Debug endpoint that leaks the shared AES encryption key."""
    user_flag = "[not accessible]"
    try:
        with open("/home/webapp/user.txt") as f:
            user_flag = f.read().strip()
    except Exception:
        pass

    return jsonify({
        "debug": True,
        "service": "config-service",
        "user_flag": user_flag,
        "config": {
            "ENCRYPTION_KEY": SHARED_AES_KEY.hex(),
            "ENCRYPTION_KEY_ASCII": SHARED_AES_KEY.decode("ascii"),
            "ENCRYPTION_ALGORITHM": "AES-128-CBC",
            "DB_HOST": "db.internal",
            "DB_PORT": 5432,
            "LOG_LEVEL": "DEBUG",
            "VAULT_URL": "http://localhost:8080",
        }
    })


@config_app.route("/debug/test-encrypt", methods=["POST"])
def debug_test_encrypt():
    """Debug endpoint to test encryption with the shared key."""
    data = request.get_json()
    if not data or "plaintext" not in data:
        return jsonify({"error": "provide 'plaintext' in JSON body"}), 400
    encrypted = encrypt_data(data["plaintext"])
    return jsonify({"plaintext": data["plaintext"], "encrypted": encrypted})


def run_vault():
    vault_app.run(host="0.0.0.0", port=8080, debug=False)


def run_config():
    config_app.run(host="0.0.0.0", port=3000, debug=False)


if __name__ == "__main__":
    # Run both services in separate threads
    t1 = threading.Thread(target=run_vault, daemon=True)
    t2 = threading.Thread(target=run_config, daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
