# J-Bot (Everyone's Jarvis)

A Teams chat bot powered by Claude Code that monitors group chats for `@jbot` messages and routes them through a stateful **Manager** session that orchestrates Claude Code worker sessions.

<!-- TODO (web-dashboard): A web dashboard for session monitoring is planned.
     It will provide real-time status, cost summaries, and worker logs via HTTP. -->

## Overview

J-Bot integrates Microsoft Teams with Claude Code to enable AI-powered task execution directly from Teams chat. When a user mentions `@jbot` in a Teams chat, the bot:

1. **Polls** Teams for new messages containing the trigger
2. **Routes** the message to the stateful Manager Claude session
3. **Executes** tasks via Claude Code worker sessions managed by the Manager
4. **Replies** with results back to Teams

This is an internal NVIDIA tool for engineering teams who need Claude Code execution capabilities within their Teams workflows.

## Architecture

### Manager Session

The bot uses a **persistent Manager session** (a long-lived Claude Code session) as the single routing brain:

- The Manager remembers all previous conversations, worker assignments, and results across restarts
- The Manager's `session_id` and dedicated chat ID are saved to the SQLite DB so bot restarts resume the same Manager instance
- All user messages from configured trigger chats flow through the Manager
- The Manager decides: answer directly (`reply`), start a new worker (`new`), resume existing worker (`resume`), or proactively report status (`report`)

### Dedicated Manager Chat

On first start, the bot creates a dedicated Teams chat for the Manager. All routing decisions and worker results are visible there. On restart, the same chat is reused (persisted in DB).

### Worker Sessions

Workers are Claude Code sessions spawned by the Manager's instructions:

- Each worker gets a `session_id` (format: `MMDD-XXXX`, e.g. `0320-a7f3`)
- Workers have access to the file system, shell commands, and Teams via `teams-cli`
- Complex tasks can get a dedicated Teams chat for their output
- Worker results are fed back to the Manager for context tracking

### Module Layout

```
src/niuma/   (internal package name)
  main.py       — CLI entry point and J-Bot lifecycle (coordinator)
  handler.py    — Inbound message routing and dispatch logic
  watcher.py    — Session watching: polls DB until worker finishes, sends result
  manager.py    — Stateful Manager session (the team lead)
  session.py    — Claude Code worker session management
  poller.py     — Teams chat polling and message parsing
  responder.py  — Sending messages back to Teams
  db.py         — SQLite database (sessions, messages, poll_state, bot_state)
  config.py     — Configuration loading and validation
  scanner.py    — Scan ~/.claude/projects/ to discover Claude sessions
  teams_api.py  — Teams API helpers (create chat, etc.)
  dispatcher.py — Legacy stateless dispatcher (kept for reference)
```

## Prerequisites

- **Python 3.9+**
- **teams-cli**: Authenticated via `teams-cli auth login`
- **claude CLI**: Authenticated via `claude auth login`
- Access to Teams chats where the bot will run
- Claude API account with model access

## Installation

Clone the repository and install in development mode:

```bash
git clone https://github.com/giftboydiyfactory/J-Bot-Everyone-s-Jarvis-.git
cd J-Bot-Everyone-s-Jarvis-
pip install -e ".[dev]"
```

## Configuration

### Setup

Create the configuration directory and copy the example config:

```bash
mkdir -p ~/.jbot
cp config.yaml.example ~/.jbot/config.yaml
```

### Get Chat ID

To find your Teams chat ID, use:

```bash
teams-cli chat list --json
```

Look for the chat you want to monitor and copy the `id` field (format: `19:xxxxx@thread.v2`).

### Edit Configuration

Open `~/.jbot/config.yaml` and update:

- **teams.chat_ids**: Add your chat IDs from the list above
- **security.allowed_users**: Add email addresses of users who can trigger the bot
- **security.admin_users**: Add email addresses of admin users (can list all sessions, stop others)
- **claude.dispatcher_model**: Model for the Manager session (default: `sonnet`)
- **claude.worker_model**: Model for executing tasks (default: `sonnet`)
- **storage.db_path**: Path to SQLite database (default: `~/.jbot/jbot.db`)

Example minimal config:

```yaml
bot:
  name: "jbot"
  trigger: "@jbot"
  emoji: "🤖"

teams:
  chat_ids:
    - "19:abc123@thread.v2"
  trigger: "@jbot"
  poll_interval: 60

claude:
  dispatcher_model: "sonnet"
  worker_model: "sonnet"
  max_concurrent: 5

security:
  allowed_users:
    - "your.email@nvidia.com"
  admin_users:
    - "your.email@nvidia.com"

storage:
  db_path: "~/.jbot/jbot.db"
```

## Running

### Foreground

Start the bot and watch logs in the current terminal:

```bash
jbot
```

### Daemon Mode

Run in the background (similar to nohup):

```bash
jbot --daemon
```

Logs are written to `~/.jbot/jbot.log`.

### Custom Config Path

Specify a non-default config file:

```bash
jbot -c /path/to/config.yaml
```

## Persistence Across Restarts

The SQLite database at `~/.jbot/jbot.db` is **persistent** — do not delete it between restarts. It stores:

- All session history and results
- The Manager's Claude `session_id` (resumed on restart)
- The Manager's dedicated Teams chat ID (reused on restart)
- Poll state (last-seen message IDs per chat — new messages only, no duplicates)
- Total cost tracking across all sessions

To check accumulated cost:

```python
from niuma.db import Database
import asyncio

async def show_cost():
    db = Database("~/.jbot/jbot.db")
    await db.init()
    total = await db.get_total_cost_usd()
    print(f"Total cost: ${total:.4f}")
    await db.close()

asyncio.run(show_cost())
```

## Graceful Shutdown

On `SIGTERM` or `SIGINT`, the bot:

1. Stops accepting new poll cycles
2. Notifies the Manager chat that shutdown is in progress
3. Waits up to 30 seconds for running worker watchers to finish
4. Cancels any remaining tasks and closes the DB connection cleanly

## Usage in Teams

Once running, use the bot in Teams by mentioning `@jbot` followed by your request:

| Command | Example | Behavior |
|---------|---------|----------|
| **New Task** | `@jbot create a Python script that prints "hello world"` | Manager delegates a new worker session |
| **Resume Session** | `@jbot continue session 0320-a7f3` | Manager resumes an existing worker session |
| **Ask Manager** | `@jbot what sessions are running?` | Manager answers from its memory |
| **Quick Reply** | `@jbot what is 2+2?` | Manager answers directly (no worker created) |

The Manager analyzes each message and determines the appropriate action. Session results are posted back to the chat when complete.

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
python3.9 -m pytest tests/ -v
```

Check coverage:

```bash
pytest --cov=src/niuma --cov-report=term-missing
```

### Project Structure Rationale

- `handler.py` contains all routing logic so `main.py` stays a thin coordinator
- `watcher.py` contains session-watching so it can be tested independently
- `manager.py` is the central brain; state is persisted via `db.py`'s `bot_state` table

## Troubleshooting

**Bot not starting**: Check `~/.jbot/jbot.log` for errors. Ensure config.yaml is valid YAML and all paths are correct.

**Messages not being detected**: Verify the chat ID is correct and the bot has access to the chat. Check that allowed_users includes the sender's email.

**teams-cli auth expired**: Run `teams-cli auth login` to refresh authentication.

**claude CLI auth expired**: Run `claude auth login` to refresh authentication.

**Sessions timing out**: Check that claude CLI is working: `claude --version`. Increase `session_timeout` in config if needed (default: 86400 seconds = 24 hours).

**Manager lost context after restart**: The Manager session_id is persisted in the DB. If the DB was deleted, the Manager starts fresh with no prior memory.
