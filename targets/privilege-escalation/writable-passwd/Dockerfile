FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install services
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        python3 \
        python3-pip \
        openssl \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Create low-priv user
RUN useradd -m -s /bin/bash ledger && \
    echo "ledger:0p3nL3dg3r_2024" | chpasswd

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Set up web application
RUN mkdir -p /var/www/app
WORKDIR /var/www/app

COPY app/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app/ .

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN mkdir -p /var/www/.config && \
    echo "SUDO{placeholder_recon_flag}" > /var/www/.config/recon_flag.txt && \
    chmod 644 /var/www/.config/recon_flag.txt

# Stage 2 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/ledger/user.txt && \
    chown ledger:ledger /home/ledger/user.txt && \
    chmod 644 /home/ledger/user.txt

# Stage 3 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# ----- Vulnerability: world-writable /etc/passwd -----
RUN chmod 666 /etc/passwd

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 22 8080

CMD ["/start.sh"]
