FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including MySQL client
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        default-mysql-client \
        sudo \
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

# Stage 1 - Recon flag
RUN mkdir -p /var/www/html/.config && \
    echo "SUDO{placeholder_recon_flag}" > /var/www/html/.config/recon_flag.txt && \
    chmod 644 /var/www/html/.config/recon_flag.txt

# Stage 2 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 3 - Root flag (readable only by root)
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# ------------------------------------------------------------------
# Debug endpoint exposes source code (intentional vulnerability)
# ------------------------------------------------------------------
RUN mkdir -p /var/www/html/debug

EXPOSE 8080

USER webapp

CMD ["python", "/app/app.py"]
