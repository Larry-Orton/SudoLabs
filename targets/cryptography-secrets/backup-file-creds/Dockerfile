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
# Create backup files (intentional vulnerability - CWE-530)
# ------------------------------------------------------------------
RUN echo '# MeridianHR Configuration File (BACKUP)\n\
# Last modified: 2024-01-15\n\
\n\
[database]\n\
db_host = localhost\n\
db_port = 5432\n\
db_name = meridianhr\n\
db_user = hr_dbadmin\n\
db_pass = HRdb_Pr0d!2024\n\
\n\
[admin]\n\
admin_user = hradmin\n\
admin_pass = M3ridian_HR!2024\n\
admin_email = admin@meridianhr.local\n\
\n\
[api]\n\
api_key = mhr-api-k3y-9f8e7d6c5b4a\n\
jwt_secret = jwt-m3ridian-s3cret-2024\n\
\n\
[smtp]\n\
smtp_host = mail.meridianhr.local\n\
smtp_user = noreply@meridianhr.local\n\
smtp_pass = Sm7p_s3nd3r!2024' > /app/config.bak

RUN echo '# Old settings file\n\
SECRET_KEY=old-s3cret-k3y-meridian\n\
ADMIN_TOKEN=mhr-tok3n-a1b2c3d4e5f6\n\
DB_CONN=postgresql://hr_dbadmin:HRdb_Pr0d!2024@localhost/meridianhr' > /app/settings.old

# ------------------------------------------------------------------
# Flag placeholder files
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN mkdir -p /var/www/html/.maintenance && \
    echo "SUDO{placeholder_recon_flag}" > /var/www/html/.maintenance/recon_flag.txt && \
    chmod 644 /var/www/html/.maintenance/recon_flag.txt

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
