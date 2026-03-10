FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Samba and SSH
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        samba \
        openssh-server \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Create users
RUN useradd -m -s /bin/bash smbuser && \
    useradd -m -s /bin/bash finance_user && \
    echo "finance_user:M3r1d1an\$hare!" | chpasswd && \
    (echo "M3r1d1an\$hare!"; echo "M3r1d1an\$hare!") | smbpasswd -a -s finance_user

# Configure SSH
RUN mkdir -p /var/run/sshd

# Create share directories
RUN mkdir -p /srv/samba/public/IT && \
    mkdir -p /srv/samba/public/general && \
    mkdir -p /srv/samba/finance/reports && \
    mkdir -p /srv/samba/finance/confidential && \
    mkdir -p /srv/samba/admin

# Public share content
RUN echo "Welcome to Meridian Financial Public Share" > /srv/samba/public/general/welcome.txt && \
    echo "=== IT Migration Notes ===" > /srv/samba/public/IT/it_migration_notes.txt && \
    echo "Date: 2024-02-01" >> /srv/samba/public/IT/it_migration_notes.txt && \
    echo "" >> /srv/samba/public/IT/it_migration_notes.txt && \
    echo "Finance share credentials (temp access for migration):" >> /srv/samba/public/IT/it_migration_notes.txt && \
    echo "  Username: finance_user" >> /srv/samba/public/IT/it_migration_notes.txt && \
    echo '  Password: M3r1d1an$hare!' >> /srv/samba/public/IT/it_migration_notes.txt && \
    echo "" >> /srv/samba/public/IT/it_migration_notes.txt && \
    echo "TODO: Remove this file after migration is complete" >> /srv/samba/public/IT/it_migration_notes.txt

# Finance share content
RUN echo "Q4 2024 Revenue: $2.3M" > /srv/samba/finance/reports/q4_report.txt

# Set permissions
RUN chmod -R 755 /srv/samba/public && \
    chown -R finance_user:finance_user /srv/samba/finance && \
    chmod -R 750 /srv/samba/finance

# Configure Samba
RUN cat > /etc/samba/smb.conf <<'EOF'
[global]
workgroup = MERIDIAN
server string = Meridian Financial File Server
security = user
map to guest = Bad User
guest account = nobody
log file = /var/log/samba/%m.log
max log size = 50

[public]
path = /srv/samba/public
browsable = yes
guest ok = yes
read only = yes
comment = Public Documents

[finance]
path = /srv/samba/finance
browsable = yes
guest ok = no
read only = yes
valid users = finance_user
comment = Finance Department

[admin]
path = /srv/samba/admin
browsable = yes
guest ok = no
read only = yes
valid users = admin
comment = Administrator Share
EOF

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN mkdir -p /opt/howl && \
    echo "SUDO{placeholder_recon_flag}" > /opt/howl/recon_flag.txt && \
    chmod 644 /opt/howl/recon_flag.txt

# Stage 2 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/smbuser/user.txt && \
    chown smbuser:smbuser /home/smbuser/user.txt && \
    chmod 644 /home/smbuser/user.txt

# Stage 3 - Root flag (in finance confidential share)
RUN echo "SUDO{placeholder_root_flag}" > /srv/samba/finance/confidential/root.txt && \
    chown finance_user:finance_user /srv/samba/finance/confidential/root.txt && \
    chmod 640 /srv/samba/finance/confidential/root.txt

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 445 22

CMD ["/start.sh"]
