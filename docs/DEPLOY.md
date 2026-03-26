# Deploying to Oracle Cloud (Always Free Tier)

## Prerequisites

- OCI account ([cloud.oracle.com](https://cloud.oracle.com) — free tier)
- SSH key pair (`ssh-keygen -t ed25519` if you don't have one)
- Repo pushed to GitHub (add remote: `git remote add origin <URL>` then `git push -u origin master`)
- Discord bot token and Anthropic API key ready

## 1. Create a Compartment (optional but recommended)

1. OCI Console → **Identity & Security** → **Compartments**
2. Click **Create Compartment**
3. Name: `discord-bot` (or use the root compartment)
4. This keeps your bot resources organized

## 2. Set Up Networking (VCN)

OCI requires a Virtual Cloud Network before creating an instance.

1. OCI Console → **Networking** → **Virtual Cloud Networks**
2. Click **Start VCN Wizard** → **Create VCN with Internet Connectivity** → **Start VCN Wizard**
3. Configure:
   - **VCN name**: `discord-bot-vcn`
   - **Compartment**: select your compartment
   - Leave CIDR blocks as defaults (`10.0.0.0/16`)
4. Click **Next** → **Create**

This creates:
- A VCN with a public subnet and private subnet
- An Internet Gateway (for outbound traffic)
- A NAT Gateway
- Default route tables and security lists

### Verify Security List

1. Go to your VCN → **Public Subnet** → **Security Lists** → **Default Security List**
2. **Ingress rules** should include:
   - SSH (port 22) from `0.0.0.0/0` — this is the default
   - (Optional) Restrict SSH source to your IP: change `0.0.0.0/0` to `YOUR_IP/32`
3. **Egress rules** should include:
   - All protocols to `0.0.0.0/0` — allows outbound HTTPS (this is the default)
4. **Do NOT** add ingress rules for HTTP/HTTPS (80/443) — the bot is not a web server

## 3. Create an Always Free Compute Instance

1. OCI Console → **Compute** → **Instances** → **Create Instance**
2. **Name**: `discord-claude-bot`
3. **Compartment**: select your compartment

### Image and Shape

4. Click **Edit** in the Image and Shape section
5. **Image**: Click **Change Image** → select **Canonical Ubuntu** → **22.04 Minimal aarch64**
6. **Shape**: Click **Change Shape**
   - Shape series: **Ampere** (ARM)
   - Shape: `VM.Standard.A1.Flex` — Always Free eligible
   - **OCPUs**: 1
   - **Memory**: 6 GB
   - (Free tier allows up to 4 OCPUs / 24 GB total across all A1 instances)

### Primary VNIC (Networking)

7. Click **Edit** in the Networking section
8. **Virtual Cloud Network**: select `discord-bot-vcn` (created in step 2)
9. **Subnet**: select the **public subnet** (`Public Subnet-discord-bot-vcn`)
10. **Public IPv4 address**: select **Assign a public IPv4 address**
    - This is required for SSH access and for the bot to reach the internet

### SSH Key

11. Click **Edit** in the SSH keys section
12. Select **Paste public keys**
13. Paste your public key (contents of `~/.ssh/id_ed25519.pub`)

### Boot Volume

14. Leave defaults (46.6 GB is fine, Always Free allows up to 200 GB total)

### Create

15. Click **Create**
16. Wait for the instance status to change to **Running**
17. Copy the **Public IP Address** from the instance details page

> **"Out of capacity" error**: ARM free tier instances are limited by regional capacity. If you get this error:
> - Try a different **Availability Domain** (AD-2 or AD-3)
> - Try a different **region** (e.g., Phoenix, Ashburn)
> - Retry later — capacity frees up periodically
> - As a fallback, use `VM.Standard.E2.1.Micro` (AMD x86, Always Free, 1 OCPU / 1 GB RAM — less powerful but more available)

## 4. SSH into the Instance

```bash
ssh ubuntu@<PUBLIC_IP>
```

If connection is refused, wait 1-2 minutes — the instance may still be booting.

If you get a "Permission denied" error, ensure:
- You're using the correct private key (`-i ~/.ssh/id_ed25519`)
- The username is `ubuntu` (not `opc` — that's for Oracle Linux images)

## 5. Server Setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip git
```

Ubuntu 22.04 ships with Python 3.10 by default.

## 6. Clone and Install

```bash
git clone <YOUR_REPO_URL> ~/discord-claude-bot
cd ~/discord-claude-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 7. Create .env

```bash
cat > ~/discord-claude-bot/.env << 'EOF'
DISCORD_BOT_TOKEN=your-token-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
BOT_CHANNELS=
EOF
chmod 600 ~/discord-claude-bot/.env
```

`chmod 600` restricts the file to owner-only access.

## 8. Test Run

```bash
cd ~/discord-claude-bot
source .venv/bin/activate
python3 bot.py
```

Verify `Logged in as ...` appears, then Ctrl+C to stop.

## 9. Set Up systemd Service (Auto-Start)

```bash
sudo cp ~/discord-claude-bot/deploy/discord-claude-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable discord-claude-bot
sudo systemctl start discord-claude-bot
sudo systemctl status discord-claude-bot
```

The bot will now auto-start on boot and restart on crashes (with a 10-second delay).

## 10. Viewing Logs

```bash
# Live log stream
sudo journalctl -u discord-claude-bot -f

# Last 100 lines
sudo journalctl -u discord-claude-bot -n 100

# Logs since last boot
sudo journalctl -u discord-claude-bot -b
```

## 11. Updating the Bot

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

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Out of capacity" on instance creation | Try different Availability Domain or region, or use AMD micro shape |
| SSH "Connection refused" | Instance still booting — wait 1-2 min |
| SSH "Permission denied" | Check key path (`-i`), username must be `ubuntu` |
| Bot starts but no Discord response | Check `journalctl` logs, verify `.env` tokens |
| Bot crashes on restart | Check `sudo systemctl status discord-claude-bot` and logs |
| Can't reach internet from instance | Verify Internet Gateway exists in VCN and egress rules allow all |

## Quick Reference

| Action | Command |
|--------|---------|
| Start | `sudo systemctl start discord-claude-bot` |
| Stop | `sudo systemctl stop discord-claude-bot` |
| Restart | `sudo systemctl restart discord-claude-bot` |
| Status | `sudo systemctl status discord-claude-bot` |
| Logs (live) | `sudo journalctl -u discord-claude-bot -f` |
| Logs (recent) | `sudo journalctl -u discord-claude-bot -n 100` |
