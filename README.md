# SudoLabs — Terminal Cybersecurity Hacking Lab

SudoLabs is a terminal-based cybersecurity hacking lab that runs entirely from your command line. It spins up vulnerable Docker targets, provides AI-powered guidance, and tracks your progress through a scoring system with hacker-themed ranks.

SudoLabs also includes **HTB Mode** for hacking external machines like HackTheBox, with built-in nmap scanning and AI-assisted walkthroughs.

## Features

- **50 Vulnerable Targets** across 5 attack categories, from beginner to elite difficulty
- **5 Attack Categories** — Web Exploitation, Network Services, Privilege Escalation, API Hacking, Cryptography & Secrets
- **Docker-Managed Labs** — Targets spin up and tear down automatically
- **AI Helper** — Powered by Claude with progressive hints, real commands, and educational explanations
- **HTB Mode** — Hack external machines (HackTheBox, TryHackMe, etc.) with AI guidance and nmap integration
- **Scoring System** — Points, time bonuses, hint penalties, and hacker-themed ranks (Script Kiddie to Zero Day)
- **11 Achievements** — First Blood, Ghost, Speed Demon, Clean Sweeps, and more
- **Beautiful Terminal UI** — Rich-powered interface with progress bars, panels, and color-coded output

## Requirements

- **Kali Linux** (recommended) or any Debian-based Linux distro
- **Python 3.10+**
- **Docker** and **Docker Compose** (for lab targets)
- **nmap** (for HTB mode scanning)
- **Anthropic API key** (for AI hints — optional but recommended)

## Installation

### One-Command Install (Kali Linux)

```bash
git clone https://github.com/Larry-Orton/SudoLabs.git
cd SudoLabs
bash install.sh
```

The installer will:
1. Check for Python 3.10+ and Docker
2. Create a virtual environment at `~/.sudolabs/venv/`
3. Install all dependencies
4. Create a `sudolabs` command in `~/.local/bin/`
5. Optionally prompt for your Anthropic API key

### Manual Install

```bash
git clone https://github.com/Larry-Orton/SudoLabs.git
cd SudoLabs
pip install -e .
```

### Set Up AI Helper (Optional)

```bash
sudolabs config --set-api-key sk-ant-your-key-here
```

Or set the environment variable:
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Usage

### Interactive Menu

Run `sudolabs` to get the interactive main menu:

```bash
sudolabs
```

The menu options are:
1. **Hunt** — Start hunting a Docker-based target
2. **HTB Mode** — Hack an external machine (HackTheBox)
3. **Targets** — Browse all available targets by category
4. **Score** — View your scores and achievements
5. **Profile** — View your hunter profile
6. **AI Chat** — Talk to the AI helper
7. **Doctor** — Check system readiness
8. **Config** — Settings and configuration
9. **Quit** — Exit SudoLabs

### Target Categories

Targets are organized into 5 attack categories:

| Category | Targets | Description |
|----------|---------|-------------|
| **Web Exploitation** | 10 | SQLi, XSS, SSRF, file uploads, command injection, LFI, deserialization |
| **Network Services** | 10 | FTP, SMB, SSH, Redis, SNMP, DNS, NFS, pivoting |
| **Privilege Escalation** | 10 | SUID, sudo, cron, PATH injection, capabilities, Docker escape, kernel |
| **API Hacking** | 10 | IDOR, JWT, GraphQL, mass assignment, CORS, OAuth, broken auth |
| **Cryptography & Secrets** | 10 | Hardcoded creds, .env exposure, git leaks, padding oracle, weak hashing |

### Hunting Docker Targets

Launch a target by name or from the interactive menu:

```bash
# Direct command
sudolabs hunt sqli-login-bypass

# Browse by category
sudolabs targets --category web-exploitation

# Or use the interactive menu
sudolabs
# Select "1" (Hunt), pick a category, then pick a target
```

During a hunt, you have these commands:

| Command | Description |
|---------|-------------|
| `ask <question>` | Ask the AI helper anything |
| `hint [1-3]` | Get a hint (1=nudge, 2=direction, 3=walkthrough). Affects score. |
| `submit <flag>` | Submit a flag (format: `SUDO{...}`) |
| `info` | Show current stage info and attack chain |
| `target` | Show target IP and ports |
| `status` | Refresh the status header |
| `clear` | Clear screen and redraw |
| `pause` | Pause and save your session |
| `abort` | Abandon the hunt |
| Any other input | Passed directly to the system shell |

### HTB Mode (HackTheBox / External Machines)

> **IMPORTANT:** If you are hacking HackTheBox machines, you must have your **OpenVPN connection running** before starting HTB mode:
> ```bash
> sudo openvpn your-htb-vpn-file.ovpn
> ```

Start an HTB session:

```bash
# Full options
sudolabs htb 10.10.11.123 --name Lame --hostname lame.htb

# Minimal (just IP)
sudolabs htb 10.10.11.123

# Or from the interactive menu: select "2" (HTB Mode)
```

**Options:**
- `--name` / `-n` — Machine name (e.g., "Lame", "Blue")
- `--hostname` / `-H` — Hostname to add to /etc/hosts (e.g., "lame.htb")
- `--no-hosts` — Skip /etc/hosts modification

**HTB Mode Commands:**

| Command | Description |
|---------|-------------|
| `ask <question>` | Ask the AI anything. It searches online and uses your scan results. |
| `hint [1-3]` | Get a hint based on your current phase. AI researches online first. |
| `scan [type]` | Run nmap (`quick`, `default`, or `full`). Results auto-feed to the AI. |
| `milestone` | Mark a pentest milestone (`recon`, `foothold`, `user`, `user_flag`, `root`, `root_flag`) |
| `info` | Show milestones and discovered services |
| `target` | Show target IP, hostname, and ports |
| `note <text>` | Save a session note |
| `notes` | View all saved notes |
| `done` | Mark the session as complete |
| `pause` | Pause the session |
| `abort` | Abandon the session |
| Any other input | Passed directly to the system shell |

**Typical HTB Workflow:**

```
sudolabs htb 10.10.11.123 --name Lame --hostname lame.htb

sudolabs/htb> scan                          # Run nmap
sudolabs/htb> ask what should I try first   # AI analyzes services
sudolabs/htb> milestone recon               # Mark recon complete
sudolabs/htb> ask how do I exploit vsftpd   # AI searches for exploits
sudolabs/htb> milestone foothold            # Got initial shell
sudolabs/htb> milestone root_flag           # Captured root.txt
sudolabs/htb> done                          # Session complete
```

### Other Commands

```bash
# List all targets
sudolabs targets
sudolabs targets --category api-hacking
sudolabs targets --difficulty easy

# View scores
sudolabs score

# View profile
sudolabs profile
sudolabs profile --set-name "YourName"

# System check
sudolabs doctor

# Reset progress
sudolabs reset sqli-login-bypass
sudolabs reset --all

# View/set config
sudolabs config
sudolabs config --set-api-key sk-ant-your-key

# Check for updates
sudolabs update
```

## AI Helper

The AI helper is powered by Anthropic's Claude and provides:

- **Progressive hints** (Level 1-3) from vague nudges to step-by-step walkthroughs
- **Free-form Q&A** — Ask anything about the current target
- **Real commands** — Uses the actual target IP and ports, never placeholders
- **Online research** (HTB mode) — Searches for walkthroughs and exploit info
- **Educational explanations** — Explains the "why" behind techniques

Hints at higher levels reduce your score on Docker targets:
- Level 1 (Nudge): -15% score multiplier
- Level 2 (Direction): -35% score multiplier
- Level 3 (Walkthrough): -60% score multiplier

In HTB mode, hints are free (no scoring penalty).

## Scoring & Ranks

**Score Formula:**
```
stage_score = base_points * hint_multiplier * time_bonus
```

**Ranks:**

| Rank | Points |
|------|--------|
| Script Kiddie | 0 - 499 |
| Hacktivist | 500 - 1,999 |
| Pentester | 2,000 - 4,999 |
| Exploit Dev | 5,000 - 9,999 |
| Red Team | 10,000 - 19,999 |
| APT Operator | 20,000 - 34,999 |
| Zero Day | 35,000+ |

## Target Difficulties

- **Easy** — Basic web vulnerabilities, default credentials, simple misconfigurations
- **Medium** — Known CVEs, service exploitation, multi-step attacks
- **Hard** — Chained exploits, binary exploitation, advanced techniques
- **Elite** — Custom exploits, real-world attack chains, multi-service pivoting

## Configuration

SudoLabs stores its config at `~/.sudolabs/`:
- `~/.sudolabs/config.yaml` — API key, username
- `~/.sudolabs/sudolabs.db` — SQLite database (scores, progress, sessions)

## Self-Update

```bash
sudolabs update
```

Pulls the latest code from GitHub and re-installs dependencies automatically.

## Troubleshooting

**Docker not running:**
```bash
sudo systemctl start docker
```

**Permission denied on Docker:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

**nmap permission issues:**
```bash
# Some scans need root
sudo nmap -sV -sC target_ip
```

**API key not working:**
```bash
sudolabs config --set-api-key sk-ant-your-new-key
```

**Run the doctor:**
```bash
sudolabs doctor
```

## License

MIT
