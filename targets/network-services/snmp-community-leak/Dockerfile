FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install SNMP daemon, SSH, Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        snmpd \
        snmp \
        openssh-server \
        python3 \
        sudo \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Create users
RUN useradd -m -s /bin/bash snmpuser && \
    useradd -m -s /bin/bash netmon && \
    echo "netmon:S3nt1n3lM0n!2024" | chpasswd

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Configure SNMP with default community string and leaked info
RUN cat > /etc/snmp/snmpd.conf <<'EOF'
# Sentinel Networking Device - SNMP Configuration
# Community string: public (default - TODO: change in production)

com2sec readonly default public

group MyROGroup v2c readonly

view all included .1

access MyROGroup "" any noauth exact all none none

sysLocation "Sentinel NOC - Rack 4B (SSH: netmon / S3nt1n3lM0n!2024 - temp access)"
sysContact admin@sentinel-networking.local
sysName sentinel-gw-01.sentinel-networking.local

# Expose process table
proc snmpd
proc sshd

# Extend with custom scripts
extend device_type /bin/echo "Sentinel SG-500 Security Gateway"
extend firmware_ver /bin/echo "v4.2.1-stable"
extend monitoring /bin/echo "netmon_agent --user=netmon --pass=S3nt1n3lM0n!2024 --interval=60"

agentaddress udp:161
EOF

# Create device directories
RUN mkdir -p /opt/sentinel/.monitoring

# Web status page
COPY app/status_page.py /app/status_page.py

# Fake monitoring script (visible in process list)
COPY app/netmon_agent.sh /opt/sentinel/netmon_agent.sh
RUN chmod +x /opt/sentinel/netmon_agent.sh

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN echo "SUDO{placeholder_recon_flag}" > /opt/sentinel/.monitoring/recon_flag.txt && \
    chmod 644 /opt/sentinel/.monitoring/recon_flag.txt

# Stage 2 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/snmpuser/user.txt && \
    chown snmpuser:snmpuser /home/snmpuser/user.txt && \
    chmod 644 /home/snmpuser/user.txt

# Stage 3 - Config flag
RUN echo "SUDO{placeholder_config_flag}" > /opt/sentinel/config_flag.txt && \
    chmod 644 /opt/sentinel/config_flag.txt

# Stage 4 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Privilege escalation vector: netmon can run find as root
RUN echo "netmon ALL=(root) NOPASSWD: /usr/bin/find" >> /etc/sudoers

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 161/udp 22 8080

CMD ["/start.sh"]
