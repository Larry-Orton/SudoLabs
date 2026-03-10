FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install NFS server, SSH
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nfs-kernel-server \
        openssh-server \
        sudo \
        rpcbind \
    && rm -rf /var/lib/apt/lists/*

# Create devops user
RUN useradd -m -s /bin/bash devops

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config

# Generate SSH key pair for devops user (the key to be stolen via NFS)
RUN mkdir -p /home/devops/.ssh && \
    ssh-keygen -t rsa -b 2048 -f /home/devops/.ssh/id_rsa -N "" -q && \
    cp /home/devops/.ssh/id_rsa.pub /home/devops/.ssh/authorized_keys && \
    chown -R devops:devops /home/devops/.ssh && \
    chmod 700 /home/devops/.ssh && \
    chmod 600 /home/devops/.ssh/id_rsa && \
    chmod 644 /home/devops/.ssh/authorized_keys

# Create shared directories
RUN mkdir -p /opt/shared && \
    mkdir -p /opt/ironclad/.nfs_config && \
    mkdir -p /opt/ironclad/internal && \
    chmod 777 /opt/shared

# Devops home content
RUN echo "=== Ironclad Storage - DevOps Workstation ===" > /home/devops/notes.txt && \
    echo "NFS shares configured for remote development" >> /home/devops/notes.txt && \
    echo "SSH key-based auth enabled" >> /home/devops/notes.txt && \
    chown devops:devops /home/devops/notes.txt

# Configure NFS exports - misconfigured with wildcard and no_root_squash
RUN echo "/home/devops *(rw,sync,no_subtree_check)" > /etc/exports && \
    echo "/opt/shared *(rw,sync,no_subtree_check,no_root_squash)" >> /etc/exports

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN echo "SUDO{placeholder_recon_flag}" > /opt/ironclad/.nfs_config/recon_flag.txt && \
    chmod 644 /opt/ironclad/.nfs_config/recon_flag.txt

# Stage 2 - User flag (in devops home, accessible via NFS)
RUN echo "SUDO{placeholder_user_flag}" > /home/devops/user.txt && \
    chown devops:devops /home/devops/user.txt && \
    chmod 644 /home/devops/user.txt

# Stage 3 - SSH access flag
RUN echo "SUDO{placeholder_ssh_flag}" > /opt/ironclad/internal/ssh_flag.txt && \
    chmod 644 /opt/ironclad/internal/ssh_flag.txt

# Stage 4 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 2049 111 22

CMD ["/start.sh"]
