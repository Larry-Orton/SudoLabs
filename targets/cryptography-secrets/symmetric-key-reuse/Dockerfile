FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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
RUN mkdir -p /var/www/html/.ops && \
    echo "SUDO{placeholder_recon_flag}" > /var/www/html/.ops/recon_flag.txt && \
    chmod 644 /var/www/html/.ops/recon_flag.txt

# Stage 2 - Vault flag
RUN mkdir -p /opt/novabridge && \
    echo "SUDO{placeholder_vault_flag}" > /opt/novabridge/vault_flag.txt && \
    chmod 644 /opt/novabridge/vault_flag.txt

# Stage 3 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 4 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

EXPOSE 8080 3000

USER webapp

CMD ["python", "/app/app.py"]
