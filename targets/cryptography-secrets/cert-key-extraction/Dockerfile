FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssl \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash webapp

WORKDIR /app

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app/ /app/

# ------------------------------------------------------------------
# Flag placeholder files
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN mkdir -p /var/www/html/.irongate && \
    echo "SUDO{placeholder_recon_flag}" > /var/www/html/.irongate/recon_flag.txt && \
    chmod 644 /var/www/html/.irongate/recon_flag.txt

# Stage 2 - Certificate analysis flag
RUN mkdir -p /opt/irongate && \
    echo "SUDO{placeholder_cert_flag}" > /opt/irongate/cert_flag.txt && \
    chmod 644 /opt/irongate/cert_flag.txt

# Stage 3 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 4 - Decryption flag
RUN echo "SUDO{placeholder_decrypt_flag}" > /opt/irongate/decrypt_flag.txt && \
    chmod 644 /opt/irongate/decrypt_flag.txt

# Stage 5 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Create certs directory
RUN mkdir -p /app/certs && chown -R webapp:webapp /app/certs

# Make init script executable
RUN chmod +x /app/init_certs.sh

EXPOSE 443 8443

# Run as root to bind to privileged ports
CMD ["python", "/app/app.py"]
