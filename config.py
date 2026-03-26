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
    "Be concise and conversational. Use Discord markdown for formatting."
)

MAX_RECENT_MESSAGES = 40
SUMMARIZE_BATCH_SIZE = 30

DB_PATH = Path(__file__).parent / "sessions.db"
