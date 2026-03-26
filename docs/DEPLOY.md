# Deployment Guide

## Option 1: Fly.io (Recommended — Free Tier)

Fly.io's free tier includes 3 shared VMs that run 24/7 — perfect for an always-on Discord bot.

### Prerequisites

- [Fly.io account](https://fly.io) (free, credit card required for verification)
- [Fly CLI](https://fly.io/docs/flyctl/install/) installed
- Repo pushed to GitHub

### 1. Install Fly CLI

```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Windows (PowerShell)
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### 2. Log In

```bash
fly auth login
```

### 3. Launch the App

From the project root:

```bash
cd discord-claude-bot
fly launch --no-deploy
```

When prompted:
- **App name**: `discord-claude-bot` (or pick a unique name)
- **Region**: pick one close to you
- **Database**: No
- **Redis**: No

This creates a `fly.toml` config file.

### 4. Set Secrets (Environment Variables)

```bash
fly secrets set DISCORD_BOT_TOKEN=your-token-here
fly secrets set ANTHROPIC_API_KEY=sk-ant-your-key-here
fly secrets set BOT_CHANNELS=ai-chat
```

Secrets are encrypted and injected as environment variables at runtime. Never put them in `fly.toml`.

### 5. Deploy

```bash
fly deploy
```

Fly builds your Dockerfile, pushes the image, and starts the bot. First deploy takes 1-2 minutes.

### 6. Verify

```bash
# Check status
fly status

# View live logs
fly logs
```

You should see `Logged in as ...` in the logs.

### Updating the Bot

```bash
# After making changes and pushing to git:
fly deploy
```

That's it — Fly rebuilds and restarts automatically.

### SQLite on Fly.io

**Important**: Fly.io VMs have ephemeral storage — the SQLite database resets on each deploy. For a personal bot this is usually fine (conversation history restarts). If you need persistent data:

- Add a [Fly Volume](https://fly.io/docs/volumes/) (1 GB free):
  ```bash
  fly volumes create bot_data --size 1 --region <your-region>
  ```
- Add to `fly.toml`:
  ```toml
  [mounts]
    source = "bot_data"
    destination = "/data"
  ```
- Update `config.py` to use `/data/sessions.db` when running on Fly:
  ```python
  import os
  DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).parent / "sessions.db"))
  ```
- Set the env var: `fly secrets set DB_PATH=/data/sessions.db`

### Useful Fly Commands

| Action | Command |
|--------|---------|
| Deploy | `fly deploy` |
| Status | `fly status` |
| Logs (live) | `fly logs` |
| SSH into VM | `fly ssh console` |
| Restart | `fly apps restart` |
| Stop | `fly scale count 0` |
| Start | `fly scale count 1` |
| View secrets | `fly secrets list` |

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Deploy fails | Check `fly logs` — usually a build error or missing secret |
| Bot not responding | Run `fly status` — is the VM running? Check `fly logs` |
| "No machines" error | Run `fly scale count 1` |
| DB resets on deploy | Add a Fly Volume (see above) |

---

## Option 2: Railway ($5/mo)

If you prefer a simpler dashboard experience:

1. Go to [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub Repo** → select `discord-claude-bot`
3. Go to **Variables** tab, add:
   - `DISCORD_BOT_TOKEN`
   - `ANTHROPIC_API_KEY`
   - `BOT_CHANNELS` (optional)
4. Railway auto-detects the Dockerfile and deploys

Updates deploy automatically when you push to GitHub.

---

## Option 3: Run Locally

For development or if you have an always-on machine:

```bash
cd discord-claude-bot
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Fill in your tokens
python bot.py
```

To keep it running in the background (Linux/macOS):

```bash
nohup python bot.py > bot.log 2>&1 &
```

---

## SQLite Database Notes

- **No setup needed** — `sessions.db` is created automatically on first run
- Uses WAL mode for better performance
- **Backup**: `cp sessions.db sessions.db.backup`
- **Reset**: stop the bot, delete `sessions.db`, `sessions.db-wal`, and `sessions.db-shm`, restart
