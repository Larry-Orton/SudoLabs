FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install services
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        python3 \
        python3-pip \
        libcap2-bin \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Create low-priv user
RUN useradd -m -s /bin/bash analyst && \
    echo "analyst:C4pSt0ne_D4ta!" | chpasswd

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
RUN echo "SUDO{placeholder_user_flag}" > /home/analyst/user.txt && \
    chown analyst:analyst /home/analyst/user.txt && \
    chmod 644 /home/analyst/user.txt

# Stage 3 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# ----- Vulnerability: cap_setuid on python3 -----
RUN setcap cap_setuid+ep /usr/bin/python3.11 || setcap cap_setuid+ep /usr/bin/python3

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 22 8080

CMD ["/start.sh"]
