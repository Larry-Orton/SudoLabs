FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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

# Create flag directories and placeholder flag files
# Stage 1: Reconnaissance flag
RUN mkdir -p /var/www/.config && \
    echo "FLAG{recon_nettools_discovered}" > /var/www/.config/recon_flag.txt && \
    chmod 644 /var/www/.config/recon_flag.txt

# Stage 2: User flag
RUN echo "FLAG{command_injection_pwned}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 3: Privilege escalation flag (readable only by root)
RUN mkdir -p /opt && \
    echo "FLAG{suid_find_discovered}" > /opt/privesc_flag.txt && \
    chmod 600 /opt/privesc_flag.txt

# Stage 4: Root flag
RUN echo "FLAG{root_shell_obtained}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Set SUID bit on find for privilege escalation path
RUN chmod u+s /usr/bin/find

# Change ownership of app directory
RUN chown -R webapp:webapp /var/www/app

# Run as webapp user
USER webapp

EXPOSE 8080

CMD ["python", "app.py"]
