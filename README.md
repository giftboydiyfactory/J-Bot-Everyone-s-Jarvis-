# J-Bot (Everyone's Jarvis)

Your AI engineering assistant, managed through Microsoft Teams chat. Powered by Claude Code (Opus 1M).

## What It Does

Type `@jbot` in a Teams chat → J-Bot reads your message → does the work → replies directly in chat.

J-Bot is a **persistent AI coordinator** with full tool access. It can:
- Query databases, read/write files, run shell commands
- Start parallel Claude Code task sessions for complex work
- Remember all conversations across restarts (1M context)
- Report progress and results directly to Teams

## Quick Start

```bash
# 1. Clone & install
git clone https://github.com/giftboydiyfactory/J-Bot-Everyone-s-Jarvis-.git
cd J-Bot-Everyone-s-Jarvis-
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Configure
mkdir -p ~/.jbot
cp config.yaml.example ~/.jbot/config.yaml
# Edit: teams.chat_ids, security.admin_users

# 3. Authenticate
teams-cli auth login
claude auth login

# 4. Run
bash scripts/start.sh
```

## Architecture

```
Teams Chat (@jbot message)
  └─ Poller (adaptive 5s→60s)
      └─ Handler (acknowledgment + forwarding)
          └─ Coordinator (persistent Opus session, --resume)
              ├─ Replies directly via teams-cli
              ├─ Queries DB, reads files, runs commands
              ├─ Starts task sessions for complex work
              └─ Reports results back to chat
```

### How It Works

1. **Poller** reads Teams chats every 5-60s (adaptive — fast when active, slow when idle)
2. **Handler** sends "Received — thinking..." and forwards the message to the Coordinator
3. **Coordinator** (Opus 1M, persistent session) decides what to do:
   - Simple questions → replies directly via `teams-cli`
   - Database queries → runs `sqlite3` and replies
   - Complex tasks → starts a Claude Code task session
4. **Task sessions** run independently, report progress, and feed results back

### Module Layout

```
src/niuma/          # Internal package name (kept for backward compat)
  main.py           # CLI entry point, polling loop, adaptive scheduling
  handler.py        # Message forwarding + error handling (simplified)
  manager.py        # Coordinator session (Opus, full tool access, direct replies)
  session.py        # Task session lifecycle (start/resume/stop)
  watcher.py        # Monitors task sessions, heartbeats, progress reporting
  poller.py         # Teams chat polling and message parsing
  responder.py      # Teams message formatting and sending
  db.py             # SQLite: sessions, messages, poll_state, bot_state
  config.py         # YAML config loading and validation
  teams_api.py      # Microsoft Graph API helpers (chat creation, members)
```

## Configuration

### `~/.jbot/config.yaml`

```yaml
bot:
  name: "jbot"
  trigger: "@jbot"
  emoji: "🤖"

teams:
  chat_ids:
    - "19:your-chat-id@thread.v2"
  poll_interval: 60      # Max interval (adaptive: starts at 5s)

claude:
  dispatcher_model: "opus"   # Coordinator model
  worker_model: "opus"       # Task session model
  max_concurrent: 5          # Max parallel task sessions
  session_timeout: 86400     # 24h
  permission_mode: "auto"
  default_cwd: "~"

security:
  allowed_users:
    - "you@nvidia.com"
  admin_users:
    - "you@nvidia.com"

storage:
  db_path: "~/.jbot/jbot.db"

logging:
  level: "INFO"
  file: "~/.jbot/jbot.log"
```

### Finding Your Chat ID

```bash
teams-cli chat list --json
```

Look for `id` field (format: `19:xxxxx@thread.v2`).

## Running

| Method | Command | Notes |
|--------|---------|-------|
| **Watchdog** (recommended) | `bash scripts/start.sh` | Auto-restart on crash, survives SSH |
| **Foreground** | `jbot` | Logs to terminal |
| **Daemon** | `jbot --daemon` | Logs to `~/.jbot/jbot.log` |
| **Stop** | `bash scripts/stop.sh` | Kills watchdog + bot |
| **Full Reset** | `bash scripts/reset.sh` | Clears all state, fresh start |

## Usage in Teams

| What You Say | What Happens |
|-------------|--------------|
| `@jbot hello` | Coordinator replies directly |
| `@jbot list my sessions` | Coordinator queries DB, replies with table |
| `@jbot analyze src/ for bugs` | Coordinator starts task session, reports findings |
| `@jbot what is 17 * 23?` | Coordinator computes and replies |
| `@jbot check CI status` | Coordinator runs commands, replies |

The Coordinator decides whether to answer directly or start a task session based on complexity.

## Features

- **Adaptive Polling**: 5s when active → gradually increases to 60s when idle
- **Persistent Memory**: Coordinator remembers all conversations across restarts (--resume)
- **Parallel Task Sessions**: Up to 5 concurrent Claude Code sessions
- **Live Progress**: 60-second heartbeats showing what task sessions are doing
- **Auto-restart Watchdog**: `start.sh` uses nohup + while loop, survives SSH disconnect
- **Self-message Detection**: Bot recognizes its own messages to prevent loops
- **Role-based Access**: Admin users get full access, members are restricted
- **Cost Tracking**: Per-session cost stored in DB
- **Skills System**: Skills in `skills/` auto-loaded into task session prompts

## Persistence

The SQLite database (`~/.jbot/jbot.db`) stores:
- Coordinator session ID (resumed on restart)
- Coordinator Teams chat ID (reused on restart)
- All task session history, results, and costs
- Poll state (last-seen message IDs per chat)

**Do not delete** `~/.jbot/jbot.db` between restarts.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (52 tests)
pytest tests/ -v

# Coverage
pytest --cov=src/niuma --cov-report=term-missing
```

## Migration from `~/.niuma/`

If upgrading from the old `niuma` naming:

```bash
bash scripts/migrate.sh
```

This copies config, DB, and logs from `~/.niuma/` to `~/.jbot/`, renaming files and updating paths.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Bot not starting | Check `~/.jbot/jbot.log` for errors |
| Messages not detected | Verify chat ID and `allowed_users` in config |
| `teams-cli` auth expired | Run `teams-cli auth login` |
| `claude` auth expired | Run `claude auth login` |
| Coordinator lost memory | Don't delete `~/.jbot/jbot.db`. Use `scripts/reset.sh` only for full reset |
| Infinite "thinking..." loop | Self-message detection failed — check "Sent by J-Bot" in bot messages |
| Task session timeout | Increase `session_timeout` in config (default: 86400s = 24h) |

## License

Internal NVIDIA tool — Interconnect Shanghai team.
