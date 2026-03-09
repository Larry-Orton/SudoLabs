# =============================================================================
# SSRF to Internal Services Target - Howl Cybersecurity Lab
# CWE-918 - Server-Side Request Forgery
# =============================================================================

FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        nmap \
        iputils-ping \
        findutils \
    && rm -rf /var/lib/apt/lists/*

# Create webapp user
RUN useradd -m -s /bin/bash webapp

# Set up application directory
WORKDIR /var/www/app

# Copy requirements and install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# ---- Plant flags ----

# Stage 1: Reconnaissance flag (readable by all)
RUN mkdir -p /var/www/.config && \
    echo "FLAG{ssrf_pr3v1ew_d1sc0v3r3d}" > /var/www/.config/recon_flag.txt && \
    chmod 644 /var/www/.config/recon_flag.txt

# Stage 2: User flag (readable by webapp user, obtained after credential theft)
RUN echo "FLAG{1nt3rn4l_s3rv1c3_cr3ds_st0l3n}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 3: Data extraction flag (readable only by root)
RUN mkdir -p /opt/secrets && \
    echo "FLAG{cmd_1nj3ct10n_d4t4_3xtr4ct3d}" > /opt/secrets/ssrf_flag.txt && \
    chmod 600 /opt/secrets/ssrf_flag.txt

# Stage 4: Root flag
RUN echo "FLAG{r00t_0wn3d_ssrf_ch41n_c0mpl3t3}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Set SUID bit on find for privilege escalation path
RUN chmod u+s /usr/bin/find

# Change ownership of app directory
RUN chown -R webapp:webapp /var/www/app

# Expose the main web application port
EXPOSE 8080

# Run as webapp user
USER webapp

CMD ["python", "app.py"]
