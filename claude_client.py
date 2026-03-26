import logging
from typing import Callable

import anthropic
import db
from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MAX_TOKENS,
    CLAUDE_MODEL,
    MAX_RECENT_MESSAGES,
    SUMMARIZE_BATCH_SIZE,
    SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

WEB_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search"},
    {"type": "web_fetch_20260209", "name": "web_fetch"},
]

CHANNEL_HISTORY_TOOL = {
    "name": "get_channel_history",
    "description": (
        "Fetch recent message history from a Discord channel in this server. "
        "Use this when a user asks you to summarize, catch up on, or review "
        "what happened in a specific channel. The channel_ref can be a "
        "#channel-name or a channel ID."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "channel_ref": {
                "type": "string",
                "description": "The channel name (e.g. 'general') or channel mention (e.g. '<#123456>')",
            },
            "hours_back": {
                "type": "integer",
                "description": "How many hours of history to fetch (max 168 = 1 week). Default 24.",
                "default": 24,
            },
        },
        "required": ["channel_ref"],
    },
}

ALL_TOOLS = WEB_TOOLS + [CHANNEL_HISTORY_TOOL]

SUMMARIZE_PROMPT = (
    "Summarize the following conversation concisely, preserving key facts, "
    "decisions, and context that would be needed to continue the conversation. "
    "If a previous summary is included, incorporate it into the new summary.\n\n"
)


def _summarize(thread_id: str):
    messages = db.get_messages(thread_id)
    batch = messages[:SUMMARIZE_BATCH_SIZE]

    previous_summary = db.get_summary(thread_id)
    text_to_summarize = ""
    if previous_summary:
        text_to_summarize += f"[Previous summary]\n{previous_summary}\n\n"
    text_to_summarize += "[Messages to summarize]\n"
    for msg in batch:
        text_to_summarize += f"{msg['role']}: {msg['content']}\n"

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": SUMMARIZE_PROMPT + text_to_summarize}],
    )
    summary = response.content[0].text
    db.update_summary_and_trim(thread_id, summary, SUMMARIZE_BATCH_SIZE)
    logger.info("Summarized and trimmed %d messages for thread %s", SUMMARIZE_BATCH_SIZE, thread_id)


def get_response(
    thread_id: str,
    user_message: str,
    tool_executor: Callable[[str, dict], str] | None = None,
) -> str:
    db.add_message(thread_id, "user", user_message)

    msg_count = db.get_message_count(thread_id)
    if msg_count > MAX_RECENT_MESSAGES:
        logger.info("Thread %s has %d messages, triggering summarization", thread_id, msg_count)
        _summarize(thread_id)

    messages = []
    summary = db.get_summary(thread_id)
    if summary:
        messages.append({
            "role": "user",
            "content": f"[Summary of earlier conversation]\n{summary}",
        })
        messages.append({
            "role": "assistant",
            "content": "Understood, I have the context from our earlier conversation.",
        })

    messages.extend(db.get_messages(thread_id))

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=ALL_TOOLS,
    )

    max_continuations = 10
    while max_continuations > 0:
        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "pause_turn":
            # Server-side tool (web search) continuation
            logger.info("Server-side tool in progress for thread %s, continuing...", thread_id)
            messages = [*messages, {"role": "assistant", "content": response.content}]
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=ALL_TOOLS,
            )
            max_continuations -= 1
            continue

        if response.stop_reason == "tool_use":
            # Custom tool call — execute and return results
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            if not tool_use_blocks or not tool_executor:
                break

            # Append assistant response with tool_use blocks
            messages = [*messages, {"role": "assistant", "content": response.content}]

            # Execute each tool and collect results
            tool_results = []
            for block in tool_use_blocks:
                logger.info("Executing tool %s for thread %s", block.name, thread_id)
                try:
                    result = tool_executor(block.name, block.input)
                except Exception as e:
                    logger.exception("Tool execution failed: %s", block.name)
                    result = f"Error executing tool: {e}"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            # Send results back to Claude
            messages.append({"role": "user", "content": tool_results})
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=ALL_TOOLS,
            )
            max_continuations -= 1
            continue

        # Unknown stop reason
        break

    # Extract text from response (may contain mixed content blocks)
    reply = "\n".join(block.text for block in response.content if block.type == "text")

    db.add_message(thread_id, "assistant", reply)
    return reply
