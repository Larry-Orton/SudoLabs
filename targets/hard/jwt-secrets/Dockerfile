FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create webapp user
RUN useradd -m -s /bin/bash webapp

# Create application directory
WORKDIR /app
COPY app/ /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# ============================================================
# Place flags at their expected paths with correct permissions
# ============================================================

# Stage 1 - Reconnaissance flag
RUN mkdir -p /var/www/.config && \
    echo "FLAG{vault_api_endpoints_mapped_d4e5f6}" > /var/www/.config/recon_flag.txt && \
    chmod 644 /var/www/.config/recon_flag.txt

# Stage 2 - JWT Forgery flag (user flag)
RUN echo "FLAG{jwt_secret_cracked_admin_forged_a1b2c3}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 3 - SSTI flag
RUN mkdir -p /opt/secrets && \
    echo "FLAG{jinja2_ssti_rce_achieved_7g8h9i}" > /opt/secrets/ssti_flag.txt && \
    chmod 644 /opt/secrets/ssti_flag.txt

# Stage 4 - Root flag (only readable by root)
RUN echo "FLAG{suid_python_root_escalation_x0y1z2}" > /root/root.txt && \
    chmod 600 /root/root.txt

# ============================================================
# Set SUID bit on python3 for privilege escalation path
# ============================================================
RUN chmod u+s /usr/local/bin/python3 && \
    chmod u+s /usr/local/bin/python3.9

# Ensure app files are owned by webapp
RUN chown -R webapp:webapp /app

EXPOSE 8080

USER webapp

CMD ["python", "/app/app.py"]
