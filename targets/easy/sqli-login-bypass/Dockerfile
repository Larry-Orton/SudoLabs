FROM python:3.9-slim

# Avoid interactive prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        sqlite3 \
        sudo \
        nmap \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create webapp user
RUN useradd -m -s /bin/bash webapp

# Create application directory
WORKDIR /app

# Copy requirements first for layer caching
COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application files
COPY app/ /app/

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag (hidden web directory)
RUN mkdir -p /var/www/html/.hidden && \
    echo "HOWL{placeholder_recon_flag}" > /var/www/html/.hidden/recon_flag.txt && \
    chmod 644 /var/www/html/.hidden/recon_flag.txt

# Stage 2 - User flag (webapp home)
RUN echo "HOWL{placeholder_user_flag}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 3 - Database secrets flag
RUN mkdir -p /opt/secrets && \
    echo "HOWL{placeholder_db_flag}" > /opt/secrets/db_flag.txt && \
    chmod 644 /opt/secrets/db_flag.txt

# Stage 4 - Root flag (only readable by root)
RUN echo "HOWL{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# ------------------------------------------------------------------
# Privilege escalation vector: sudo misconfiguration
# webapp can run sqlite3 as root without a password
# ------------------------------------------------------------------
RUN echo "webapp ALL=(root) NOPASSWD: /usr/bin/sqlite3" >> /etc/sudoers

# Static files served from /var/www/html (for recon discovery)
RUN mkdir -p /var/www/html/assets && \
    echo '<!DOCTYPE html><html><body><h1>Nexus Corp</h1></body></html>' > /var/www/html/index.html

# Ensure the database directory is writable
RUN mkdir -p /app/data && chown webapp:webapp /app/data

# Expose the web application port
EXPOSE 8080

# Run as webapp user
USER webapp

CMD ["python", "/app/app.py"]
