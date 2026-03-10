FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gnupg \
        curl \
        python3 \
        python3-pip \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Install MongoDB
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
    gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg && \
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
    tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && \
    apt-get install -y mongodb-org && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps for web app
RUN pip3 install --no-cache-dir flask pymongo bcrypt

# Create app user
RUN useradd -m -s /bin/bash appuser

# Configure MongoDB - bind to all interfaces, no auth
RUN mkdir -p /data/db && \
    chown -R mongodb:mongodb /data/db && \
    sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf

# Web application
RUN mkdir -p /opt/datapulse/.internal && \
    mkdir -p /opt/datapulse/admin_flag

COPY app/webapp.py /app/webapp.py
COPY app/init_mongo.py /app/init_mongo.py
COPY app/templates/ /app/templates/

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN echo "SUDO{placeholder_recon_flag}" > /opt/datapulse/.internal/recon_flag.txt && \
    chmod 644 /opt/datapulse/.internal/recon_flag.txt

# Stage 2 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/appuser/user.txt && \
    chown appuser:appuser /home/appuser/user.txt && \
    chmod 644 /home/appuser/user.txt

# Stage 3 - Root flag (admin panel)
RUN echo "SUDO{placeholder_root_flag}" > /opt/datapulse/admin_flag/root.txt && \
    chmod 644 /opt/datapulse/admin_flag/root.txt

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 27017 3000

CMD ["/start.sh"]
