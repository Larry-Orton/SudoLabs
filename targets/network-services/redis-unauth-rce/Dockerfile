FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Redis, SSH, Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        redis-server \
        openssh-server \
        python3 \
        python3-pip \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps for web app
RUN pip3 install --no-cache-dir flask redis

# Create redis user with home directory and SSH support
RUN usermod -m -d /home/redis -s /bin/bash redis && \
    mkdir -p /home/redis/.ssh && \
    chown -R redis:redis /home/redis && \
    chmod 700 /home/redis/.ssh

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Configure Redis - bind to all interfaces, no auth
RUN sed -i 's/^bind .*/bind 0.0.0.0/' /etc/redis/redis.conf && \
    sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf && \
    sed -i 's/^daemonize yes/daemonize no/' /etc/redis/redis.conf

# Web application
RUN mkdir -p /var/www/app/.debug
COPY app/webapp.py /var/www/app/webapp.py
COPY app/init_redis.py /var/www/app/init_redis.py

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN echo "SUDO{placeholder_recon_flag}" > /var/www/app/.debug/recon_flag.txt && \
    chmod 644 /var/www/app/.debug/recon_flag.txt

# Stage 2 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/redis/user.txt && \
    chown redis:redis /home/redis/user.txt && \
    chmod 644 /home/redis/user.txt

# Stage 3 - SSH injection flag
RUN mkdir -p /opt/cacheflow && \
    echo "SUDO{placeholder_ssh_flag}" > /opt/cacheflow/ssh_flag.txt && \
    chmod 644 /opt/cacheflow/ssh_flag.txt

# Stage 4 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Privilege escalation vector: redis user can run redis-cli as root
RUN echo "redis ALL=(root) NOPASSWD: /usr/bin/redis-cli" >> /etc/sudoers

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 6379 8080 22

CMD ["/start.sh"]
