# Deploying to Oracle Cloud (Always Free Tier)

## Prerequisites

- OCI account ([cloud.oracle.com](https://cloud.oracle.com) — free tier)
- SSH key pair (`ssh-keygen -t ed25519` if you don't have one)
- Repo pushed to GitHub (add remote: `git remote add origin <URL>` then `git push -u origin master`)
- Discord bot token and Anthropic API key ready

## 1. Create an Always Free Instance

1. OCI Console → **Compute** → **Instances** → **Create Instance**
2. **Image**: Canonical Ubuntu 22.04 Minimal (aarch64)
3. **Shape**: `VM.Standard.A1.Flex` (Ampere ARM) — Always Free eligible
   - Set to **1 OCPU, 6 GB RAM** (plenty for this bot)
4. **Boot volume**: 50 GB
5. **Networking**: Use default VCN, public IP assigned automatically
6. **SSH key**: Paste your public key (`~/.ssh/id_ed25519.pub`)

> **Note**: ARM free tier instances can be hard to provision due to capacity. If you get "Out of capacity", retry later or try a different availability domain.

## 2. SSH and Server Setup

```bash
ssh ubuntu@<PUBLIC_IP>

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip git
```

Ubuntu 22.04 ships with Python 3.10 by default.

## 3. Clone and Install

```bash
git clone <YOUR_REPO_URL> ~/discord-claude-bot
cd ~/discord-claude-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Create .env

```bash
cat > ~/discord-claude-bot/.env << 'EOF'
DISCORD_BOT_TOKEN=your-token-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
EOF
chmod 600 ~/discord-claude-bot/.env
```

`chmod 600` restricts the file to owner-only access.

## 5. Test Run

```bash
cd ~/discord-claude-bot
source .venv/bin/activate
python3 bot.py
```

Verify `Logged in as ...` appears, then Ctrl+C to stop.

## 6. Set Up systemd Service (Auto-Start)

```bash
sudo cp ~/discord-claude-bot/deploy/discord-claude-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable discord-claude-bot
sudo systemctl start discord-claude-bot
sudo systemctl status discord-claude-bot
```

The bot will now auto-start on boot and restart on crashes (with a 10-second delay).

## 7. Viewing Logs

```bash
# Live log stream
sudo journalctl -u discord-claude-bot -f

# Last 100 lines
sudo journalctl -u discord-claude-bot -n 100

# Logs since last boot
sudo journalctl -u discord-claude-bot -b
```

## 8. Updating the Bot

```bash
cd ~/discord-claude-bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart discord-claude-bot
sudo systemctl status discord-claude-bot
```

## SQLite Database

- **No setup needed** — `sessions.db` is created automatically on first run by `db.init_db()`
- Data persists on disk at `/home/ubuntu/discord-claude-bot/sessions.db`
- Uses WAL mode for better performance
- **Backup**: `cp sessions.db sessions.db.backup` (safe while bot is running)
- **Reset**: stop the bot, delete `sessions.db`, `sessions.db-wal`, and `sessions.db-shm`, then restart

## Firewall Notes

- The bot only makes **outbound** HTTPS connections (port 443). No inbound ports need to be opened.
- OCI's default Security List allows all outbound traffic + SSH inbound (port 22). This is sufficient.
- **Do NOT** open inbound HTTP/HTTPS — the bot is not a web server.
- To harden: restrict SSH ingress in OCI Security List to your home IP only.

## Quick Reference

| Action | Command |
|--------|---------|
| Start | `sudo systemctl start discord-claude-bot` |
| Stop | `sudo systemctl stop discord-claude-bot` |
| Restart | `sudo systemctl restart discord-claude-bot` |
| Status | `sudo systemctl status discord-claude-bot` |
| Logs (live) | `sudo journalctl -u discord-claude-bot -f` |
| Logs (recent) | `sudo journalctl -u discord-claude-bot -n 100` |
