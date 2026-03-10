FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install OpenVPN, web server deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openvpn \
        easy-rsa \
        python3 \
        python3-pip \
        openssl \
        curl \
        sudo \
        iptables \
    && rm -rf /var/lib/apt/lists/*

# Install Python web deps
RUN pip3 install --no-cache-dir flask requests

# Create directories
RUN mkdir -p /opt/obsidian/vpn && \
    mkdir -p /opt/obsidian/certs && \
    mkdir -p /opt/obsidian/internal && \
    mkdir -p /opt/obsidian/admin && \
    mkdir -p /var/www/portal/.hidden && \
    mkdir -p /var/www/portal/downloads && \
    mkdir -p /etc/openvpn/server

# Generate self-signed CA and server certs
RUN openssl genrsa -out /etc/openvpn/server/ca.key 2048 && \
    openssl req -new -x509 -days 365 -key /etc/openvpn/server/ca.key \
        -out /etc/openvpn/server/ca.crt \
        -subj "/C=US/ST=VA/O=Obsidian Security/CN=obsidian-vpn-ca.internal.corp" && \
    openssl genrsa -out /etc/openvpn/server/server.key 2048 && \
    openssl req -new -key /etc/openvpn/server/server.key \
        -out /etc/openvpn/server/server.csr \
        -subj "/C=US/ST=VA/O=Obsidian Security/CN=vpn-gw.obsidian.local" && \
    openssl x509 -req -days 365 -in /etc/openvpn/server/server.csr \
        -CA /etc/openvpn/server/ca.crt -CAkey /etc/openvpn/server/ca.key \
        -CAcreateserial -out /etc/openvpn/server/server.crt && \
    openssl dhparam -out /etc/openvpn/server/dh2048.pem 1024

# Create client config (downloadable, with weak settings)
RUN cat > /var/www/portal/downloads/client.ovpn <<'OVPN'
# Obsidian Security Corp - VPN Client Configuration
# WARNING: This is a pre-configured profile for quick onboarding
client
dev tun
proto udp
remote vpn-gw.obsidian.local 1194
resolv-retry infinite
nobind
persist-key
persist-tun
# NOTE: Certificate verification relaxed for compatibility
# verify-x509-name is DISABLED - accepting any server cert
# This is a known issue - ticket SEC-2847
cipher AES-128-CBC
auth SHA1
verb 3
# Internal network routes
# route 10.8.0.0 255.255.255.0
# Admin panel: 10.8.0.2:9090
# API server: 10.8.0.1:8080
<ca>
OVPN
cat /etc/openvpn/server/ca.crt >> /var/www/portal/downloads/client.ovpn && \
    echo "</ca>" >> /var/www/portal/downloads/client.ovpn

# Web portal application
COPY app/portal.py /app/portal.py
COPY app/internal_admin.py /app/internal_admin.py
COPY app/templates/ /app/templates/

# ------------------------------------------------------------------
# Flag placeholder files (Howl engine replaces these at session start)
# ------------------------------------------------------------------

# Stage 1 - Recon flag
RUN echo "SUDO{placeholder_recon_flag}" > /var/www/portal/.hidden/recon_flag.txt && \
    chmod 644 /var/www/portal/.hidden/recon_flag.txt

# Stage 2 - VPN config analysis flag
RUN echo "SUDO{placeholder_config_flag}" > /opt/obsidian/vpn/config_flag.txt && \
    chmod 644 /opt/obsidian/vpn/config_flag.txt

# Stage 3 - Certificate weakness flag
RUN echo "SUDO{placeholder_cert_flag}" > /opt/obsidian/certs/cert_flag.txt && \
    chmod 644 /opt/obsidian/certs/cert_flag.txt

# Stage 4 - SSRF pivot flag
RUN echo "SUDO{placeholder_pivot_flag}" > /opt/obsidian/internal/pivot_flag.txt && \
    chmod 644 /opt/obsidian/internal/pivot_flag.txt

# Stage 5 - Root flag (internal admin)
RUN echo "SUDO{placeholder_root_flag}" > /opt/obsidian/admin/root.txt && \
    chmod 644 /opt/obsidian/admin/root.txt

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 1194/udp 443

CMD ["/start.sh"]
