import logging
import re
from datetime import datetime, timedelta, timezone

import discord
from config import (
    CHANNEL_HISTORY_MAX_CHARS,
    CHANNEL_HISTORY_MAX_HOURS,
    CHANNEL_HISTORY_MAX_MESSAGES,
)

logger = logging.getLogger(__name__)


async def resolve_channel(guild: discord.Guild, channel_ref: str) -> discord.TextChannel | None:
    """Resolve a channel reference (name, #name, or <#id>) to a TextChannel."""
    # Handle Discord channel mention format: <#123456789>
    match = re.match(r"<#(\d+)>", channel_ref)
    if match:
        channel = guild.get_channel(int(match.group(1)))
        if isinstance(channel, discord.TextChannel):
            return channel
        return None

    # Strip leading # if present
    name = channel_ref.lstrip("#").strip().lower()

    for channel in guild.text_channels:
        if channel.name.lower() == name:
            return channel

    return None


async def fetch_channel_history(
    channel: discord.TextChannel,
    hours_back: int,
    max_messages: int = CHANNEL_HISTORY_MAX_MESSAGES,
) -> str:
    """Fetch and format recent messages from a channel."""
    hours_back = min(hours_back, CHANNEL_HISTORY_MAX_HOURS)
    after = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    try:
        messages = []
        async for msg in channel.history(after=after, limit=max_messages, oldest_first=True):
            # Skip bot messages and empty messages
            if msg.author.bot or not msg.content:
                continue
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
            messages.append(f"[{timestamp}] {msg.author.display_name}: {msg.content}")
    except discord.Forbidden:
        return f"Error: I don't have permission to read message history in #{channel.name}."

    if not messages:
        return f"No messages found in #{channel.name} in the last {hours_back} hours."

    result = f"Message history from #{channel.name} (last {hours_back} hours, {len(messages)} messages):\n\n"
    result += "\n".join(messages)

    # Truncate from the oldest end if too large
    if len(result) > CHANNEL_HISTORY_MAX_CHARS:
        lines = result.split("\n")
        # Keep header + newest messages that fit
        header = lines[0] + "\n"
        truncated = [f"[Truncated: oldest messages removed to fit context limit]\n"]
        current_len = len(header) + len(truncated[0])

        # Add lines from newest to oldest, then reverse
        kept = []
        for line in reversed(lines[1:]):
            if current_len + len(line) + 1 > CHANNEL_HISTORY_MAX_CHARS:
                break
            kept.append(line)
            current_len += len(line) + 1

        result = header + truncated[0] + "\n".join(reversed(kept))

    return result
