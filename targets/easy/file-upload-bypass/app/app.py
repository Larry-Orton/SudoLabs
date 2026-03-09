"""PixShare - Photo Sharing Platform (Vulnerable to Unrestricted File Upload).

CWE-434: Unrestricted Upload of File with Dangerous Type

The application accepts any file type without validation, and a hidden admin
endpoint can execute uploaded Python scripts, leading to remote code execution.
"""

import io
import os
import sys

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

app = Flask(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ------------------------------------------------------------------ #
# Public routes
# ------------------------------------------------------------------ #


@app.route("/")
def index():
    """Home page -- upload form and gallery of uploaded files."""
    files = []
    if os.path.isdir(UPLOAD_DIR):
        files = sorted(os.listdir(UPLOAD_DIR))
    return render_template("index.html", files=files)


@app.route("/upload", methods=["POST"])
def upload():
    """Handle file upload -- VULNERABLE: no file type validation (CWE-434).

    Accepts any file regardless of extension, MIME type, or content.
    Files are saved directly to the uploads directory with their original name.
    """
    uploaded = request.files.get("file")

    if not uploaded or uploaded.filename == "":
        return redirect(url_for("index"))

    # VULNERABLE: Original filename used with no sanitization beyond
    # Werkzeug's secure_filename, no extension check, no MIME check.
    from werkzeug.utils import secure_filename

    filename = secure_filename(uploaded.filename)
    if not filename:
        return redirect(url_for("index"))

    save_path = os.path.join(UPLOAD_DIR, filename)
    uploaded.save(save_path)

    return redirect(url_for("index"))


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Serve uploaded files directly from the uploads directory."""
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/gallery")
def gallery():
    """Gallery view -- lists all uploaded files with links."""
    files = []
    if os.path.isdir(UPLOAD_DIR):
        files = sorted(os.listdir(UPLOAD_DIR))
    return render_template("index.html", files=files)


# ------------------------------------------------------------------ #
# Hidden admin endpoint -- the critical vulnerability
# ------------------------------------------------------------------ #


@app.route("/admin")
def admin_panel():
    """Hidden admin panel (discoverable via directory enumeration)."""
    return render_template("admin.html")


@app.route("/admin/execute")
def admin_execute():
    """VULNERABLE: Executes an arbitrary file as Python code.

    This endpoint was left over from development and allows executing any
    file on the server as a Python script. Combined with the unrestricted
    upload, this gives an attacker full remote code execution.

    Attack path:
      1. Upload a .py file via /upload
      2. GET /admin/execute?file=/app/uploads/malicious.py
      3. The server reads and exec()s the file contents
    """
    file_path = request.args.get("file", "")

    if not file_path:
        return (
            "<h3>Admin Script Runner</h3>"
            "<p>Usage: /admin/execute?file=/path/to/script.py</p>"
            "<p>Example: /admin/execute?file=/app/uploads/check.py</p>"
        ), 200

    if not os.path.isfile(file_path):
        return f"<h3>Error</h3><p>File not found: {file_path}</p>", 404

    # Capture stdout from the executed script
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()

    try:
        with open(file_path, "r") as f:
            code = f.read()
        exec(code)  # noqa: S102 -- intentionally vulnerable
        output = captured.getvalue()
    except Exception as e:
        output = f"Execution error: {str(e)}"
    finally:
        sys.stdout = old_stdout

    return (
        f"<h3>Script Output</h3><pre>{output}</pre>"
        f"<p><a href='/admin'>Back to Admin</a></p>"
    ), 200


# ------------------------------------------------------------------ #
# Entry point
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
