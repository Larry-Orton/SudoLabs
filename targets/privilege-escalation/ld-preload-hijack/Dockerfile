FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install services
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        python3 \
        python3-pip \
        gcc \
        libc6-dev \
        sudo \
        iputils-ping \
        apache2 \
    && rm -rf /var/lib/apt/lists/*

# Create low-priv user
RUN useradd -m -s /bin/bash preload && \
    echo "preload:Pr3L0ad_Dyn#2024" | chpasswd

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Store credentials in a file discoverable via command injection
RUN mkdir -p /opt && \
    echo "SSH Credentials:" > /opt/.credentials && \
    echo "  User: preload" >> /opt/.credentials && \
    echo "  Pass: Pr3L0ad_Dyn#2024" >> /opt/.credentials

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
RUN echo "SUDO{placeholder_user_flag}" > /home/preload/user.txt && \
    chown preload:preload /home/preload/user.txt && \
    chmod 644 /home/preload/user.txt

# Stage 3 - Privesc discovery flag
RUN echo "SUDO{placeholder_privesc_flag}" > /opt/.privesc_flag.txt && \
    chmod 644 /opt/.privesc_flag.txt

# Stage 4 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# ----- Vulnerability: sudo with env_keep for LD_PRELOAD -----
RUN echo 'Defaults    env_keep += "LD_PRELOAD"' >> /etc/sudoers && \
    echo 'preload ALL=(root) NOPASSWD: /usr/sbin/apache2' >> /etc/sudoers

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 22 8080

CMD ["/start.sh"]
