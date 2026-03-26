import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 4096

SYSTEM_PROMPT = (
    "You are a helpful assistant in a Discord chat. "
    "Be concise and conversational. Use Discord markdown for formatting. "
    "You can fetch message history from any channel in this Discord server "
    "using the get_channel_history tool. Use it when users ask you to "
    "summarize, catch up on, or review what happened in a channel."
)

MAX_RECENT_MESSAGES = 40
SUMMARIZE_BATCH_SIZE = 30

DB_PATH = Path(__file__).parent / "sessions.db"

THREAD_NAME_LIMIT = 100

# Comma-separated channel names the bot is allowed to respond in.
# If empty, the bot responds in all channels.
_bot_channels = os.getenv("BOT_CHANNELS", "")
BOT_CHANNELS = [ch.strip() for ch in _bot_channels.split(",") if ch.strip()]

CHANNEL_HISTORY_MAX_MESSAGES = 500
CHANNEL_HISTORY_MAX_CHARS = 80_000
CHANNEL_HISTORY_MAX_HOURS = 168  # 1 week
