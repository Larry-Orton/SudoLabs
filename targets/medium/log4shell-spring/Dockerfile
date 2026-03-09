# =============================================================================
# Log4Shell Spring Boot Target - Howl Cybersecurity Lab
# CVE-2021-44228 - Apache Log4j JNDI Injection
# =============================================================================

# ---------------------
# Stage 1: Build
# ---------------------
FROM maven:3.8-openjdk-8 AS builder

WORKDIR /build
COPY app/pom.xml .
# Download dependencies first (layer caching)
RUN mvn dependency:go-offline -B

COPY app/src ./src
RUN mvn package -DskipTests -B

# ---------------------
# Stage 2: Runtime
# ---------------------
FROM openjdk:8-jre-slim

# Install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        sudo \
        curl \
        netcat-openbsd \
        procps && \
    rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -m -s /bin/bash app

# Configure sudo - app user can run /usr/bin/find as root without password
RUN echo "app ALL=(root) NOPASSWD: /usr/bin/find" > /etc/sudoers.d/app-find && \
    chmod 0440 /etc/sudoers.d/app-find

# Create application directory
RUN mkdir -p /opt/app

# Copy the built JAR from builder stage
COPY --from=builder /build/target/*.jar /opt/app/inventory-api.jar

# ---- Plant flags ----
# Recon flag - readable by all (discovered during reconnaissance)
RUN echo "FLAG{sp1ng_b00t_r3c0n_d1sc0v3r3d}" > /opt/app/recon_flag.txt && \
    chmod 644 /opt/app/recon_flag.txt

# User flag - readable by app user (obtained after initial access)
RUN echo "FLAG{l0g4sh3ll_jnd1_rc3_ach13v3d}" > /home/app/user.txt && \
    chown app:app /home/app/user.txt && \
    chmod 600 /home/app/user.txt

# Escalation flag - readable only by root (obtained after priv esc)
RUN echo "FLAG{sud0_f1nd_pr1v3sc_succ3ss}" > /opt/escalation_flag.txt && \
    chmod 600 /opt/escalation_flag.txt

# Root flag - readable only by root (final objective)
RUN echo "FLAG{r00t_0wn3d_l0g4sh3ll_c0mpl3t3}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Set ownership of app directory
RUN chown -R app:app /opt/app

WORKDIR /opt/app

# Expose the Spring Boot default port
EXPOSE 8080

# Run as the app user
USER app

# Start the application
# JAVA_OPTS is set via docker-compose environment for JNDI trust settings
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /opt/app/inventory-api.jar"]
