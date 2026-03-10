FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create webapp user
RUN useradd -m -s /bin/bash webapp

WORKDIR /app

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app/ /app/

# ------------------------------------------------------------------
# Create the .env file (intentional vulnerability - CWE-538)
# ------------------------------------------------------------------
RUN echo 'APP_NAME=CloudPulse Analytics\n\
APP_ENV=production\n\
APP_DEBUG=false\n\
APP_SECRET_KEY=cp-s3cr3t-k3y-x7m9p2q4\n\
\n\
DB_HOST=localhost\n\
DB_PORT=5432\n\
DB_NAME=cloudpulse\n\
DB_USER=cpdb_admin\n\
DB_PASSWORD=Cl0udDB!_pr0d2024\n\
\n\
ADMIN_USERNAME=cloudadmin\n\
ADMIN_PASSWORD=Puls3_@dmin!2024\n\
\n\
STRIPE_API_KEY=FAKE_STRIPE_KEY_FOR_CTF_CHALLENGE\n\
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n\
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n\
\n\
REDIS_URL=redis://localhost:6379/0\n\
SMTP_PASSWORD=mailgun_s3nd3r!99' > /app/.env

# ------------------------------------------------------------------
# Flag placeholder files
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN mkdir -p /var/www/html/.backup && \
    echo "SUDO{placeholder_recon_flag}" > /var/www/html/.backup/recon_flag.txt && \
    chmod 644 /var/www/html/.backup/recon_flag.txt

# Stage 2 - User flag
RUN echo "SUDO{placeholder_user_flag}" > /home/webapp/user.txt && \
    chown webapp:webapp /home/webapp/user.txt && \
    chmod 644 /home/webapp/user.txt

# Stage 3 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

EXPOSE 8080

USER webapp

CMD ["python", "/app/app.py"]
