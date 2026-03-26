import asyncio
import logging

import discord
import claude_client
import db
from config import BOT_CHANNELS, DISCORD_BOT_TOKEN, THREAD_NAME_LIMIT
from utils import setup_logging, split_message

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    logger.info("Logged in as %s", client.user)

    if BOT_CHANNELS:
        for guild in client.guilds:
            existing = {ch.name for ch in guild.text_channels}
            for channel_name in BOT_CHANNELS:
                if channel_name not in existing:
                    try:
                        await guild.create_text_channel(channel_name)
                        logger.info("Created channel #%s in %s", channel_name, guild.name)
                    except discord.Forbidden:
                        logger.warning("Missing permission to create #%s in %s", channel_name, guild.name)
                else:
                    logger.info("Channel #%s already exists in %s", channel_name, guild.name)
        logger.info("Bot restricted to channels: %s", ", ".join(BOT_CHANNELS))
    else:
        logger.info("No BOT_CHANNELS set — responding in all channels")


@client.event
async def on_message(message: discord.Message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Determine the base channel (parent for threads, channel itself otherwise)
    if isinstance(message.channel, discord.Thread):
        base_channel = message.channel.parent
    else:
        base_channel = message.channel

    # If BOT_CHANNELS is set, ignore messages outside allowed channels
    if BOT_CHANNELS and hasattr(base_channel, "name") and base_channel.name not in BOT_CHANNELS:
        return

    # Case 1: Message in a bot-owned thread
    if isinstance(message.channel, discord.Thread) and message.channel.owner_id == client.user.id:
        thread = message.channel
        try:
            async with thread.typing():
                reply = await asyncio.to_thread(
                    claude_client.get_response, str(thread.id), message.content
                )
            for chunk in split_message(reply):
                await thread.send(chunk)
        except Exception:
            logger.exception("Error in thread response")
            await thread.send("Sorry, something went wrong. Check the bot logs.")
        return

    # Case 2: Bot is mentioned in a channel
    if client.user in message.mentions:
        # Strip the mention to get the actual message content
        content = message.content.replace(f"<@{client.user.id}>", "").strip()
        content = content.replace(f"<@!{client.user.id}>", "").strip()

        if not content:
            await message.reply("Mention me with a message to start a conversation!")
            return

        # Create a thread from the message
        thread_name = content[:THREAD_NAME_LIMIT]
        thread = await message.create_thread(name=thread_name)

        try:
            async with thread.typing():
                reply = await asyncio.to_thread(
                    claude_client.get_response, str(thread.id), content
                )
            for chunk in split_message(reply):
                await thread.send(chunk)
        except Exception:
            logger.exception("Error in mention response")
            await thread.send("Sorry, something went wrong. Check the bot logs.")


if __name__ == "__main__":
    setup_logging()
    db.init_db()
    logger.info("Starting bot...")
    client.run(DISCORD_BOT_TOKEN)
