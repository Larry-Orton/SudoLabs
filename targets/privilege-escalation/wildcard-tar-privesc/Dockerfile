FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install services
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        python3 \
        python3-pip \
        cron \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Create low-priv user
RUN useradd -m -s /bin/bash backupuser && \
    echo "backupuser:T4rP1t_Bkup#2024" | chpasswd

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Create user-writable data directory and backup destination
RUN mkdir -p /home/backupuser/data && \
    chown backupuser:backupuser /home/backupuser/data && \
    echo "sample data file 1" > /home/backupuser/data/report1.txt && \
    echo "sample data file 2" > /home/backupuser/data/report2.txt && \
    chown backupuser:backupuser /home/backupuser/data/*.txt && \
    mkdir -p /backup

# Create the vulnerable backup script
RUN echo '#!/bin/bash' > /opt/backup.sh && \
    echo '# Backup script - runs as root via cron' >> /opt/backup.sh && \
    echo 'cd /home/backupuser/data && tar cf /backup/archive.tar *' >> /opt/backup.sh && \
    chmod 755 /opt/backup.sh

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
RUN echo "SUDO{placeholder_user_flag}" > /home/backupuser/user.txt && \
    chown backupuser:backupuser /home/backupuser/user.txt && \
    chmod 644 /home/backupuser/user.txt

# Stage 3 - Backup discovery flag
RUN echo "SUDO{placeholder_backup_flag}" > /opt/.backup_flag.txt && \
    chmod 644 /opt/.backup_flag.txt

# Stage 4 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# ----- Vulnerability: root cron job with tar wildcard -----
RUN echo "* * * * * root /opt/backup.sh" >> /etc/crontab

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 22 8080

CMD ["/start.sh"]
