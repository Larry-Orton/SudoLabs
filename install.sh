#!/bin/bash
#
# Howl - Cybersecurity Hacking Lab Installer
# One-command installation for Kali Linux / Debian / Ubuntu
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

HOWL_HOME="$HOME/.howl"
HOWL_VENV="$HOWL_HOME/venv"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo -e "${RED}${BOLD}"
echo '  ██╗  ██╗ ██████╗ ██╗    ██╗██╗     '
echo '  ██║  ██║██╔═══██╗██║    ██║██║     '
echo '  ███████║██║   ██║██║ █╗ ██║██║     '
echo '  ██╔══██║██║   ██║██║███╗██║██║     '
echo '  ██║  ██║╚██████╔╝╚███╔███╔╝███████╗'
echo '  ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝'
echo -e "${NC}"
echo -e "  ${CYAN}Cybersecurity Hacking Lab - Installer${NC}"
echo ""

# ── Check Python ───────────────────────────────────────────
echo -e "  ${BOLD}Checking requirements...${NC}"

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$cmd"
            echo -e "  ${GREEN}✓${NC} Python $version"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${RED}✗${NC} Python 3.10+ is required but not found."
    echo "  Install it with: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# ── Check pip ──────────────────────────────────────────────
if ! "$PYTHON" -m pip --version &> /dev/null; then
    echo -e "  ${RED}✗${NC} pip is not installed."
    echo "  Install it with: sudo apt install python3-pip"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} pip"

# ── Check venv ─────────────────────────────────────────────
if ! "$PYTHON" -m venv --help &> /dev/null 2>&1; then
    echo -e "  ${YELLOW}!${NC} python3-venv not found, installing..."
    sudo apt install -y python3-venv 2>/dev/null || true
fi

# ── Check Docker ───────────────────────────────────────────
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Docker (running)"
    else
        echo -e "  ${YELLOW}!${NC} Docker installed but not running."
        echo "    Start it with: sudo systemctl start docker"
    fi
else
    echo -e "  ${RED}✗${NC} Docker is not installed."
    echo "  Install it with: sudo apt install docker.io docker-compose-plugin"
    exit 1
fi

# ── Check docker compose ──────────────────────────────────
if docker compose version &> /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Docker Compose"
elif docker-compose version &> /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Docker Compose (legacy)"
else
    echo -e "  ${RED}✗${NC} Docker Compose not found."
    echo "  Install it with: sudo apt install docker-compose-plugin"
    exit 1
fi

# ── Create virtual environment ─────────────────────────────
echo ""
echo -e "  ${BOLD}Setting up Howl...${NC}"

mkdir -p "$HOWL_HOME"

if [ ! -d "$HOWL_VENV" ]; then
    echo -e "  Creating virtual environment..."
    "$PYTHON" -m venv "$HOWL_VENV"
fi

# ── Install dependencies ──────────────────────────────────
echo -e "  Installing dependencies..."
"$HOWL_VENV/bin/pip" install --quiet --upgrade pip
"$HOWL_VENV/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

# ── Install Howl package ──────────────────────────────────
echo -e "  Installing Howl..."
"$HOWL_VENV/bin/pip" install --quiet -e "$SCRIPT_DIR"

# ── Create howl wrapper script ────────────────────────────
HOWL_BIN="$HOME/.local/bin/howl"
mkdir -p "$(dirname "$HOWL_BIN")"

cat > "$HOWL_BIN" << 'WRAPPER'
#!/bin/bash
HOWL_VENV="$HOME/.howl/venv"
exec "$HOWL_VENV/bin/python" -m howl "$@"
WRAPPER

chmod +x "$HOWL_BIN"

# ── Check PATH ─────────────────────────────────────────────
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo -e "  ${YELLOW}!${NC} Add ~/.local/bin to your PATH:"
    echo '    echo '\''export PATH="$HOME/.local/bin:$PATH"'\'' >> ~/.bashrc && source ~/.bashrc'
fi

# ── API Key (optional) ────────────────────────────────────
echo ""
echo -e "  ${BOLD}AI Helper Setup (optional)${NC}"
echo -e "  The AI helper uses Anthropic's Claude API for intelligent hints."
echo -e "  You can set this up later with: ${CYAN}howl config --set-api-key${NC}"
echo ""
read -p "  Enter your Anthropic API key (or press Enter to skip): " api_key

if [ -n "$api_key" ]; then
    "$HOWL_VENV/bin/python" -c "
from howl.config import set_api_key
set_api_key('$api_key')
print('  API key saved.')
"
fi

# ── Done ──────────────────────────────────────────────────
echo ""
echo -e "  ${GREEN}${BOLD}Installation complete!${NC}"
echo ""
echo -e "  Run ${CYAN}${BOLD}howl${NC} to start hunting."
echo -e "  Run ${CYAN}howl doctor${NC} to verify your setup."
echo -e "  Run ${CYAN}howl targets${NC} to browse available targets."
echo ""
echo -e "  ${RED}${BOLD}The hunt begins now.${NC}"
echo ""
