"""NetTools Pro - Network Diagnostic Tool (Vulnerable to Command Injection)."""

import os
import subprocess

from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    """Home page for NetTools Pro."""
    return render_template("index.html")


@app.route("/ping", methods=["GET", "POST"])
def ping():
    """Ping utility endpoint - VULNERABLE to OS command injection (CWE-78).

    User input is passed directly into a shell command with no sanitization.
    """
    output = None
    ip_address = ""

    if request.method == "POST":
        ip_address = request.form.get("ip", "").strip()

        if ip_address:
            # VULNERABLE: User input passed directly to shell command
            # An attacker can inject arbitrary commands using ; | ` $() etc.
            try:
                result = subprocess.run(
                    f"ping -c 4 {ip_address}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                output = result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                output = "Error: Ping request timed out."
            except Exception as e:
                output = f"Error executing ping: {str(e)}"
        else:
            output = "Please enter a valid IP address or hostname."

    return render_template("ping.html", output=output, ip_address=ip_address)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
