import logging

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


def get_response(thread_id: str, user_message: str) -> str:
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
        tools=WEB_TOOLS,
    )

    # Handle pause_turn: server-side tools may need continuation
    max_continuations = 5
    while response.stop_reason == "pause_turn" and max_continuations > 0:
        logger.info("Web search in progress for thread %s, continuing...", thread_id)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[
                *messages,
                {"role": "assistant", "content": response.content},
            ],
            tools=WEB_TOOLS,
        )
        max_continuations -= 1

    # Extract text from response (may contain mixed content blocks)
    reply = "\n".join(block.text for block in response.content if block.type == "text")

    db.add_message(thread_id, "assistant", reply)
    return reply
