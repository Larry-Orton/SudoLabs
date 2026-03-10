FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install BIND9, web server, SSH
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bind9 \
        bind9-utils \
        python3 \
        openssh-server \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Create users
RUN useradd -m -s /bin/bash dnsadmin

# Configure SSH
RUN mkdir -p /var/run/sshd

# Configure BIND9 - allow zone transfers to anyone
RUN cat > /etc/bind/named.conf.options <<'EOF'
options {
    directory "/var/cache/bind";
    allow-query { any; };
    allow-transfer { any; };
    allow-recursion { any; };
    listen-on { any; };
    listen-on-v6 { none; };
};
EOF

RUN cat > /etc/bind/named.conf.local <<'EOF'
zone "prismnet.local" {
    type master;
    file "/etc/bind/zones/prismnet.local.zone";
    allow-transfer { any; };
};
EOF

# Create zone file with hidden subdomains
RUN mkdir -p /etc/bind/zones && \
    cat > /etc/bind/zones/prismnet.local.zone <<'EOF'
$TTL 86400
@       IN      SOA     ns1.prismnet.local. admin.prismnet.local. (
                        2024010101  ; Serial
                        3600        ; Refresh
                        900         ; Retry
                        604800      ; Expire
                        86400 )     ; Minimum TTL

        IN      NS      ns1.prismnet.local.
        IN      A       127.0.0.1

ns1             IN      A       127.0.0.1
www             IN      A       127.0.0.1
mail            IN      A       127.0.0.1
vpn             IN      A       127.0.0.1
secret-admin    IN      A       127.0.0.1
dev-staging     IN      A       127.0.0.1
internal-api    IN      A       127.0.0.1
EOF

RUN chown -R bind:bind /etc/bind/zones

# Web server content
RUN mkdir -p /var/www/html/.config && \
    mkdir -p /var/www/secret-admin

COPY app/web_server.py /app/web_server.py

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN echo "SUDO{placeholder_recon_flag}" > /var/www/html/.config/recon_flag.txt && \
    chmod 644 /var/www/html/.config/recon_flag.txt

# Stage 2 - Zone transfer flag
RUN mkdir -p /opt/dns && \
    echo "SUDO{placeholder_zone_flag}" > /opt/dns/zone_flag.txt && \
    chmod 644 /opt/dns/zone_flag.txt

# Stage 3 - Root flag (hidden admin service)
RUN echo "SUDO{placeholder_root_flag}" > /var/www/secret-admin/root.txt && \
    chmod 644 /var/www/secret-admin/root.txt

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 53/tcp 53/udp 8080 22

CMD ["/start.sh"]
