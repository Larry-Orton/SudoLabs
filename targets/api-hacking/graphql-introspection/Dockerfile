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
    echo "SUDO{placeholder_recon_flag}" > /var/www/.config/recon_flag.txt && \
    chmod 644 /var/www/.config/recon_flag.txt

# Stage 2 - Introspection flag
RUN mkdir -p /opt/secrets && \
    echo "SUDO{placeholder_introspection_flag}" > /opt/secrets/introspection_flag.txt && \
    chmod 644 /opt/secrets/introspection_flag.txt

# Stage 3 - SQL injection user flag
RUN echo "SUDO{placeholder_user_flag}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 4 - Root flag (credential extraction)
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Ensure app files are owned by webapp
RUN chown -R webapp:webapp /app

EXPOSE 4000

USER webapp

CMD ["python", "/app/app.py"]
