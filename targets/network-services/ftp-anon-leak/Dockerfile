FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install services
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        vsftpd \
        openssh-server \
        python3 \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Create users
RUN useradd -m -s /bin/bash ftpuser && \
    useradd -m -s /bin/bash sysadmin && \
    echo "sysadmin:V4ultL1n3!2024" | chpasswd

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Configure vsftpd for anonymous access
RUN mkdir -p /var/ftp/pub/backups && \
    cat > /etc/vsftpd.conf <<'EOF'
listen=YES
listen_port=21
anonymous_enable=YES
local_enable=NO
write_enable=NO
anon_root=/var/ftp
no_anon_password=YES
hide_ids=YES
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=40100
seccomp_sandbox=NO
EOF

# Create FTP content - credential leak
RUN echo "=== Vaultline Systems Backup Credentials ===" > /var/ftp/pub/backups/backup_creds.txt && \
    echo "Last updated: 2024-01-15" >> /var/ftp/pub/backups/backup_creds.txt && \
    echo "" >> /var/ftp/pub/backups/backup_creds.txt && \
    echo "SSH Access:" >> /var/ftp/pub/backups/backup_creds.txt && \
    echo "  User: sysadmin" >> /var/ftp/pub/backups/backup_creds.txt && \
    echo "  Pass: V4ultL1n3!2024" >> /var/ftp/pub/backups/backup_creds.txt && \
    echo "" >> /var/ftp/pub/backups/backup_creds.txt && \
    echo "NOTE: Change these credentials after migration is complete!" >> /var/ftp/pub/backups/backup_creds.txt

RUN echo "Vaultline Systems - FTP Archive" > /var/ftp/pub/readme.txt && \
    echo "Contact: it-support@vaultline.local" >> /var/ftp/pub/readme.txt

# Web status page
RUN mkdir -p /var/www/html/.status

COPY app/status_page.py /app/status_page.py

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag (hidden in web status page directory)
RUN echo "SUDO{placeholder_recon_flag}" > /var/www/html/.status/recon_flag.txt && \
    chmod 644 /var/www/html/.status/recon_flag.txt

# Stage 2 - User flag (ftpuser home)
RUN echo "SUDO{placeholder_user_flag}" > /home/ftpuser/user.txt && \
    chown ftpuser:ftpuser /home/ftpuser/user.txt && \
    chmod 644 /home/ftpuser/user.txt

# Stage 3 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Privilege escalation vector: sysadmin can run cat as root
RUN echo "sysadmin ALL=(root) NOPASSWD: /usr/bin/cat" >> /etc/sudoers

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 21 22 8080

CMD ["/start.sh"]
