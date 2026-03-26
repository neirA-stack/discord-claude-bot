import discord
import claude_client
import db
from config import DISCORD_BOT_TOKEN


def split_message(text: str, limit: int = 2000) -> list[str]:
    """Split text into chunks under the limit, preferring newline boundaries."""
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        # Find the last newline within the limit
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            # No newline found — split at the limit
            split_at = limit

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    return chunks


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Case 1: Message in a bot-owned thread
    if isinstance(message.channel, discord.Thread) and message.channel.owner_id == client.user.id:
        thread = message.channel
        async with thread.typing():
            reply = claude_client.get_response(str(thread.id), message.content)
        for chunk in split_message(reply):
            await thread.send(chunk)
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
        thread_name = content[:100]
        thread = await message.create_thread(name=thread_name)

        async with thread.typing():
            reply = claude_client.get_response(str(thread.id), content)
        for chunk in split_message(reply):
            await thread.send(chunk)


if __name__ == "__main__":
    db.init_db()
    client.run(DISCORD_BOT_TOKEN)
