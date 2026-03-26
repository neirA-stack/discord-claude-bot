# Feature Roadmap

Ideas for future enhancements, organized by effort level.

## Quick Wins (config/param changes)

- [ ] **Adaptive thinking** — Add `thinking: {"type": "adaptive"}` to API calls for better reasoning on complex questions
- [ ] **Prompt caching** — Add `cache_control` to system prompt to reduce API costs on repeated calls
- [ ] **Citations** — Enable source citations when web search returns results

## Medium Effort (new functionality)

- [ ] **Image understanding** — Handle Discord message attachments (images), pass them to Claude's vision API so the bot can "see" and discuss images users share
- [ ] **File/PDF analysis** — Handle document attachments (PDF, DOCX, CSV), upload via Files API for Claude to read and summarize
- [ ] **Per-channel system prompts** — Configure different bot personalities or behaviors per channel (e.g. coding helper in #dev, casual in #general)

## Larger Projects (custom tool implementation)

- [ ] **Git repo interaction** — Custom tools for reading files, running commands against a repo (read_file, search_code, etc.)
- [ ] **Code execution (custom)** — Self-hosted code runner that can access local resources, unlike the sandboxed server-side tool
- [ ] **Streaming responses** — Send tokens as they arrive for faster perceived response time (requires reworking Discord message sending)
