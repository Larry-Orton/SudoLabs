FROM python:3.9-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        docker.io \
    && rm -rf /var/lib/apt/lists/*

# Set up web application
RUN mkdir -p /var/www/app
WORKDIR /var/www/app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN mkdir -p /var/www/.config && \
    echo "SUDO{placeholder_recon_flag}" > /var/www/.config/recon_flag.txt && \
    chmod 644 /var/www/.config/recon_flag.txt

# Stage 2 - Docker discovery flag
RUN mkdir -p /opt && \
    echo "SUDO{placeholder_docker_flag}" > /opt/.docker_flag.txt && \
    chmod 644 /opt/.docker_flag.txt

# Stage 3 - Escape flag
RUN echo "SUDO{placeholder_escape_flag}" > /opt/.escape_flag.txt && \
    chmod 644 /opt/.escape_flag.txt

# Stage 4 - Root flag (this simulates the host root flag)
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

EXPOSE 8080

CMD ["python", "app.py"]
