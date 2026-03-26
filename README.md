# Discord Claude Bot

A Discord bot powered by Claude (Anthropic API). Mention the bot to start a threaded conversation with full conversation memory.

## Features

- Creates Discord threads for each conversation
- Automatic replies within bot-owned threads (no @mention needed)
- Conversation memory with summarize-and-trim (SQLite-backed)
- Splits long responses across multiple messages

## Quick Start

1. **Clone and set up a virtual environment:**
   ```bash
   git clone <repo-url>
   cd discord-claude-bot
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Fill in your `DISCORD_BOT_TOKEN` and `ANTHROPIC_API_KEY` in `.env`.

3. **Set up Discord bot:**
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application and bot
   - Enable **Message Content Intent** under Bot settings
   - Invite the bot to your server with `Send Messages`, `Create Public Threads`, and `Read Message History` permissions

4. **Run:**
   ```bash
   python bot.py
   ```

## Usage

- **@mention the bot** in any channel to start a conversation (a thread is created automatically)
- **Reply in the thread** to continue chatting (no @mention needed)
- The bot shows a typing indicator while generating a response

## Configuration

Edit `config.py` to adjust:

| Setting | Default | Description |
|---------|---------|-------------|
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Claude model to use |
| `CLAUDE_MAX_TOKENS` | `4096` | Max tokens per response |
| `MAX_RECENT_MESSAGES` | `40` | Threshold to trigger summarization |
| `SUMMARIZE_BATCH_SIZE` | `30` | Number of oldest messages to summarize |
