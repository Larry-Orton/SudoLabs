FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        coreutils \
    && rm -rf /var/lib/apt/lists/*

# Create webapp user
RUN useradd -m -s /bin/bash webapp

# Set up application directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create the uploads directory
RUN mkdir -p /app/uploads && \
    chown webapp:webapp /app/uploads

# ---------------------------------------------------------
# Flag placement
# ---------------------------------------------------------

# Stage 1: Reconnaissance flag (world-readable, hidden path)
RUN mkdir -p /var/www/.config && \
    echo "FLAG{pixshare_recon_uploads_found}" > /var/www/.config/recon_flag.txt && \
    chmod 644 /var/www/.config/recon_flag.txt

# Stage 2: User flag (readable by webapp user)
RUN echo "FLAG{unrestricted_upload_rce_achieved}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 3: Privilege escalation flag (root-only)
RUN mkdir -p /opt && \
    echo "FLAG{suid_cp_privesc_success}" > /opt/privesc_flag.txt && \
    chmod 600 /opt/privesc_flag.txt

# Stage 4: Root flag (root-only)
RUN echo "FLAG{root_pixshare_pwned}" > /root/root.txt && \
    chmod 600 /root/root.txt

# ---------------------------------------------------------
# SUID misconfiguration: cp with SUID bit
# ---------------------------------------------------------
RUN chmod u+s /usr/bin/cp

# Set ownership of the application directory
RUN chown -R webapp:webapp /app

# Run as webapp user
USER webapp

EXPOSE 8080

CMD ["python", "app.py"]
