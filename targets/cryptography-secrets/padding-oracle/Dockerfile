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
RUN mkdir -p /var/www/html/.secure && \
    echo "SUDO{placeholder_recon_flag}" > /var/www/html/.secure/recon_flag.txt && \
    chmod 644 /var/www/html/.secure/recon_flag.txt

# Stage 2 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 3 - Crypto flag
RUN mkdir -p /opt/secureauth && \
    echo "SUDO{placeholder_crypto_flag}" > /opt/secureauth/crypto_flag.txt && \
    chmod 644 /opt/secureauth/crypto_flag.txt

# Stage 4 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

EXPOSE 8080

USER webapp

CMD ["python", "/app/app.py"]
