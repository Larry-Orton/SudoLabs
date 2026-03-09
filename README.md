# Howl - Terminal Cybersecurity Hacking Lab

Howl is a terminal-based cybersecurity hacking lab that runs entirely from your command line. It manages vulnerable Docker targets, provides AI-powered guidance, and tracks your progress through a scoring system with achievements.

Howl also supports **HTB Mode** for hacking external machines like HackTheBox, with built-in nmap scanning and AI-assisted walkthroughs.

## Features

- **40 Vulnerable Targets** - 10 Easy, 10 Medium, 10 Hard, 10 Elite difficulty machines with real CVEs
- **Docker-Managed Labs** - Targets spin up and tear down automatically. You never touch Docker directly.
- **AI Helper** - Powered by Claude, provides progressive hints and answers questions with real commands you can copy-paste
- **HTB Mode** - Hack external machines (HackTheBox, TryHackMe, etc.) with AI guidance, nmap integration, and automatic /etc/hosts management
- **Scoring System** - Points, time bonuses, hint penalties, and wolf-themed ranks (Pup to Apex Howler)
- **11 Achievements** - First Blood, Ghost, Speed Demon, Clean Sweeps, and more
- **Beautiful Terminal UI** - Rich-powered interface with progress bars, panels, and color-coded output

## Requirements

- **Kali Linux** (recommended) or any Debian-based Linux distro
- **Python 3.10+**
- **Docker** and **Docker Compose** (for lab targets)
- **nmap** (for HTB mode scanning)
- **Anthropic API key** (for AI hints - optional but recommended)

## Installation

### One-Command Install (Kali Linux)

```bash
git clone https://github.com/yourusername/howl.git
cd howl
bash install.sh
```

The installer will:
1. Check for Python 3.10+ and Docker
2. Create a virtual environment at `~/.howl/venv/`
3. Install all dependencies
4. Create a `howl` command in `~/.local/bin/`
5. Optionally prompt for your Anthropic API key

### Manual Install

```bash
git clone https://github.com/yourusername/howl.git
cd howl
pip install -e .
```

### Set Up AI Helper (Optional)

```bash
howl config --set-api-key sk-ant-your-key-here
```

Or set the environment variable:
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Usage

### Interactive Menu

Just run `howl` to get the interactive main menu:

```bash
howl
```

The menu options are:
1. **Hunt** - Start hunting a Docker-based target
2. **HTB Mode** - Hack an external machine (HackTheBox)
3. **Targets** - Browse all available targets
4. **Score** - View your scores and achievements
5. **Profile** - View your hunter profile
6. **AI Chat** - Talk to the AI helper
7. **Doctor** - Check system readiness
8. **Config** - Settings and configuration
9. **Quit** - Exit Howl

### Hunting Docker Targets

Launch a target by name or from the interactive menu:

```bash
# Direct command
howl hunt sqli-login-bypass

# Or use the interactive menu
howl
# Select "1" (Hunt), then pick a target by number
```

During a hunt, you have these commands:

| Command | Description |
|---------|-------------|
| `ask <question>` | Ask the AI helper anything (e.g., `ask what nmap command should I run`) |
| `hint [1-3]` | Get a hint (1=nudge, 2=direction, 3=walkthrough). Affects score. |
| `submit <flag>` | Submit a flag (format: `HOWL{...}`) |
| `info` | Show current stage info and attack chain |
| `target` | Show target IP and ports |
| `status` | Refresh the status header |
| `clear` | Clear screen and redraw |
| `pause` | Pause and save your session |
| `abort` | Abandon the hunt |
| Any other input | Passed directly to the system shell (e.g., `nmap -sV 10.10.11.123`) |

### HTB Mode (HackTheBox / External Machines)

> **IMPORTANT:** If you are hacking HackTheBox machines, you must have your **OpenVPN connection running** before starting HTB mode. Connect to HTB's VPN first:
> ```bash
> sudo openvpn your-htb-vpn-file.ovpn
> ```
> Verify your VPN is connected by checking for a `tun0` interface: `ip addr show tun0`

Start an HTB session:

```bash
# Direct command with all options
howl htb 10.10.11.123 --name Lame --hostname lame.htb

# Minimal (just IP)
howl htb 10.10.11.123

# Or from the interactive menu: select "2" (HTB Mode)
```

**Options:**
- `--name` / `-n` - Machine name (e.g., "Lame", "Blue")
- `--hostname` / `-H` - Hostname to add to /etc/hosts (e.g., "lame.htb")
- `--no-hosts` - Skip /etc/hosts modification

**HTB Mode Commands:**

| Command | Description |
|---------|-------------|
| `ask <question>` | Ask the AI anything. It searches online for walkthroughs and uses your scan results for context. |
| `hint [1-3]` | Get a hint based on your current phase. The AI researches the machine online first. |
| `scan [type]` | Run nmap (`quick`, `default`, or `full`). Results auto-feed to the AI. |
| `milestone` | Mark a pentest milestone (`recon`, `foothold`, `user`, `user_flag`, `root`, `root_flag`) |
| `info` | Show milestones and discovered services |
| `target` | Show target IP, hostname, and ports |
| `status` | Refresh the status header |
| `clear` | Clear screen and redraw |
| `note <text>` | Save a session note |
| `notes` | View all saved notes |
| `done` | Mark the session as complete |
| `pause` | Pause the session |
| `abort` | Abandon the session |
| Any other input | Passed directly to the system shell (e.g., `nmap -sV 10.10.11.123`) |

**Typical HTB Workflow:**

```
howl htb 10.10.11.123 --name Lame --hostname lame.htb

howl/htb> scan                          # Run nmap, results feed to AI
howl/htb> ask what should I try first   # AI analyzes services and suggests next steps
howl/htb> milestone recon               # Mark recon complete
howl/htb> ask how do I exploit vsftpd   # AI searches online for specific exploits
howl/htb> milestone foothold            # Got initial shell
howl/htb> ask how do I escalate         # AI guides privilege escalation
howl/htb> milestone user_flag           # Captured user.txt
howl/htb> milestone root_flag           # Captured root.txt
howl/htb> done                          # Session complete
```

### Other Commands

```bash
# List all targets
howl targets
howl targets --difficulty easy

# View scores
howl score
howl score sqli-login-bypass  # Detailed score for a target

# View profile
howl profile
howl profile --set-name "YourName"

# System check
howl doctor

# Reset progress
howl reset sqli-login-bypass
howl reset --all

# View/set config
howl config
howl config --set-api-key sk-ant-your-key
```

## AI Helper

The AI helper is powered by Anthropic's Claude and provides:

- **Progressive hints** (Level 1-3) that adjust detail from vague nudges to step-by-step walkthroughs
- **Free-form Q&A** - Ask anything about the current target
- **Real commands** - Always uses the actual target IP and ports, never placeholders
- **Online research** (HTB mode) - Searches for walkthroughs and exploit info to give accurate, machine-specific guidance
- **Educational explanations** - Explains the "why" behind techniques, not just the "how"

Hints at higher levels reduce your score on Docker targets:
- Level 1 (Nudge): -15% score multiplier
- Level 2 (Direction): -35% score multiplier
- Level 3 (Walkthrough): -60% score multiplier

In HTB mode, hints are free (no scoring penalty) since it is a learning-focused mode.

## Scoring & Ranks

**Score Formula:**
```
stage_score = base_points * hint_multiplier * time_bonus
```

**Ranks (Wolf Theme):**

| Rank | Points |
|------|--------|
| Pup | 0 - 499 |
| Prowler | 500 - 1,999 |
| Stalker | 2,000 - 4,999 |
| Predator | 5,000 - 9,999 |
| Alpha | 10,000 - 19,999 |
| Dire Wolf | 20,000 - 34,999 |
| Apex Howler | 35,000+ |

## Target Difficulties

- **Easy** - Basic web vulnerabilities (SQLi, command injection, XSS)
- **Medium** - Known CVEs, service exploitation (Log4Shell, Apache Struts)
- **Hard** - Multi-step attacks, chained exploits, binary exploitation
- **Elite** - Advanced techniques, custom exploits, real-world attack chains

## Configuration

Howl stores its config at `~/.howl/`:
- `~/.howl/config.yaml` - API key, username
- `~/.howl/howl.db` - SQLite database (scores, progress, sessions)

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
howl config --set-api-key sk-ant-your-new-key
```

**Run the doctor:**
```bash
howl doctor
```

## License

MIT
