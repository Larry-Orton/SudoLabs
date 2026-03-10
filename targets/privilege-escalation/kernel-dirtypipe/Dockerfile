FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install services
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        python3 \
        python3-pip \
        gcc \
        libc6-dev \
        sudo \
        iputils-ping \
        openssl \
    && rm -rf /var/lib/apt/lists/*

# Create low-priv user
RUN useradd -m -s /bin/bash kerneluser && \
    echo "kerneluser:K3rn3lS3c_2024!" | chpasswd

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Store SSH credentials for discovery via command injection
RUN echo "SSH Credentials:" > /opt/.ssh_credentials && \
    echo "  User: kerneluser" >> /opt/.ssh_credentials && \
    echo "  Pass: K3rn3lS3c_2024!" >> /opt/.ssh_credentials

# Create a simulated DirtyPipe exploit binary
# This is a simulation - it doesn't exploit the actual kernel vulnerability
# Instead it uses the SUID bit to simulate the effect of CVE-2022-0847
RUN mkdir -p /opt/exploits && \
    cat > /tmp/dirtypipe_sim.c << 'EXPLOIT_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Simulated DirtyPipe (CVE-2022-0847) Exploit
 * =============================================
 * In a real scenario, this exploit abuses a flaw in the Linux pipe
 * subsystem to overwrite read-only files. This simulation uses SUID
 * to achieve the same effect for educational purposes.
 *
 * Usage:
 *   ./dirtypipe --help          Show help
 *   ./dirtypipe --auto          Auto-exploit /etc/passwd and drop to root shell
 *   ./dirtypipe <file> <offset> <data>  Overwrite file at offset with data
 */

void print_help() {
    printf("DirtyPipe Exploit Simulator (CVE-2022-0847)\n");
    printf("============================================\n");
    printf("Usage:\n");
    printf("  ./dirtypipe --help              Show this help\n");
    printf("  ./dirtypipe --auto              Auto-exploit and drop to root shell\n");
    printf("  ./dirtypipe <file> <offset> <data>  Write data to file at offset\n");
    printf("\nExample:\n");
    printf("  ./dirtypipe /etc/passwd 0 'root::0:0:root:/root:/bin/bash'\n");
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        print_help();
        return 1;
    }

    if (strcmp(argv[1], "--help") == 0) {
        print_help();
        return 0;
    }

    /* Escalate to root (simulating the kernel exploit effect) */
    setuid(0);
    setgid(0);

    if (strcmp(argv[1], "--auto") == 0) {
        printf("[*] DirtyPipe CVE-2022-0847 Exploit\n");
        printf("[*] Target kernel: 5.16.11 (VULNERABLE)\n");
        printf("[*] Overwriting /etc/passwd to inject root user...\n");

        /* Generate password hash for 'dirtypipe' */
        FILE *f = fopen("/etc/passwd", "a");
        if (f == NULL) {
            printf("[-] Failed to open /etc/passwd\n");
            return 1;
        }
        fprintf(f, "dirtypipe:$1$dp$Ks8rJwG5m9FfVpYP3.SZi0:0:0:DirtyPipe Root:/root:/bin/bash\n");
        fclose(f);

        printf("[+] Injected user 'dirtypipe' with UID 0\n");
        printf("[+] Password: dirtypipe\n");
        printf("[*] Spawning root shell...\n\n");

        /* Drop to root shell */
        char *shell_args[] = {"/bin/bash", NULL};
        execvp("/bin/bash", shell_args);
        return 0;
    }

    /* Manual mode: write data to file */
    if (argc < 4) {
        printf("Error: Manual mode requires <file> <offset> <data>\n");
        print_help();
        return 1;
    }

    char *target_file = argv[1];
    int offset = atoi(argv[2]);
    char *data = argv[3];

    printf("[*] DirtyPipe CVE-2022-0847 Exploit\n");
    printf("[*] Target: %s (offset: %d)\n", target_file, offset);
    printf("[*] Writing %zu bytes...\n", strlen(data));

    FILE *f = fopen(target_file, "r+");
    if (f == NULL) {
        printf("[-] Failed to open %s\n", target_file);
        return 1;
    }

    fseek(f, offset, SEEK_SET);
    fwrite(data, 1, strlen(data), f);
    fclose(f);

    printf("[+] Write successful!\n");
    return 0;
}
EXPLOIT_EOF
    gcc -o /opt/exploits/dirtypipe /tmp/dirtypipe_sim.c && \
    chmod u+s /opt/exploits/dirtypipe && \
    chown root:root /opt/exploits/dirtypipe && \
    rm /tmp/dirtypipe_sim.c

# Create a fake kernel version file to make it look like a vulnerable kernel
RUN echo "5.16.11-vulnerable" > /proc_version_fake && \
    echo '#!/bin/bash' > /usr/local/bin/uname && \
    echo 'if [ "$1" = "-r" ] || [ "$1" = "--kernel-release" ]; then' >> /usr/local/bin/uname && \
    echo '    echo "5.16.11"' >> /usr/local/bin/uname && \
    echo 'elif [ "$1" = "-a" ] || [ "$1" = "--all" ]; then' >> /usr/local/bin/uname && \
    echo '    echo "Linux kernelsec 5.16.11 #1 SMP PREEMPT Thu Mar 3 2022 x86_64 GNU/Linux"' >> /usr/local/bin/uname && \
    echo 'else' >> /usr/local/bin/uname && \
    echo '    /bin/uname "$@"' >> /usr/local/bin/uname && \
    echo 'fi' >> /usr/local/bin/uname && \
    chmod +x /usr/local/bin/uname

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
RUN echo "SUDO{placeholder_user_flag}" > /home/kerneluser/user.txt && \
    chown kerneluser:kerneluser /home/kerneluser/user.txt && \
    chmod 644 /home/kerneluser/user.txt

# Stage 3 - Kernel discovery flag
RUN echo "SUDO{placeholder_kernel_flag}" > /opt/.kernel_flag.txt && \
    chmod 644 /opt/.kernel_flag.txt

# Stage 4 - Root flag
RUN echo "SUDO{placeholder_root_flag}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Startup script
COPY app/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 22 8080

CMD ["/start.sh"]
