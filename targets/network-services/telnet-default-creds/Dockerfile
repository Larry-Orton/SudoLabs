FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install telnet server and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        xinetd \
        telnetd \
        python3 \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Create operator user with default credentials
RUN useradd -m -s /bin/bash operator && \
    echo "operator:Gr1dIr0n" | chpasswd

# Configure telnet via xinetd
RUN cat > /etc/xinetd.d/telnet <<'EOF'
service telnet
{
    disable         = no
    flags           = REUSE
    socket_type     = stream
    wait            = no
    user            = root
    server          = /usr/sbin/in.telnetd
    log_on_failure  += USERID
}
EOF

# Create device simulation directories
RUN mkdir -p /opt/device/.system && \
    mkdir -p /opt/device/config && \
    mkdir -p /opt/device/logs && \
    mkdir -p /opt/device/backups/.config_backup && \
    mkdir -p /opt/device/firmware

# Device configuration files (decoys and real content)
RUN echo "GridIron GX-3000 Industrial Controller" > /opt/device/config/device_info.txt && \
    echo "Firmware: v2.4.1" >> /opt/device/config/device_info.txt && \
    echo "Serial: GX3K-2024-00847" >> /opt/device/config/device_info.txt

RUN echo "[2024-01-15] System boot" > /opt/device/logs/system.log && \
    echo "[2024-01-15] Telnet service started" >> /opt/device/logs/system.log && \
    echo "[2024-01-15] Web dashboard started" >> /opt/device/logs/system.log && \
    echo "[2024-01-16] Config backup created" >> /opt/device/logs/system.log

# Web dashboard
COPY app/dashboard.py /app/dashboard.py

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag (hidden in device system directory)
RUN echo "SUDO{placeholder_recon_flag}" > /opt/device/.system/recon_flag.txt && \
    chmod 644 /opt/device/.system/recon_flag.txt

# Stage 2 - User flag (operator home)
RUN echo "SUDO{placeholder_user_flag}" > /home/operator/user.txt && \
    chown operator:operator /home/operator/user.txt && \
    chmod 644 /home/operator/user.txt

# Stage 3 - Root flag (hidden in config backup)
RUN echo "SUDO{placeholder_root_flag}" > /opt/device/backups/.config_backup/root.txt && \
    chmod 644 /opt/device/backups/.config_backup/root.txt

# Allow telnet connections (remove securetty restrictions)
RUN cp /dev/null /etc/securetty 2>/dev/null; true

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 23 8080

CMD ["/start.sh"]
