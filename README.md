# niuma-bot

A Teams chat bot powered by Claude Code that monitors group chats for `@niuma` messages and dispatches them to Claude for execution.

## Overview

niuma-bot integrates Microsoft Teams with Claude Code to enable AI-powered task execution directly from Teams chat. When a user mentions `@niuma` in a Teams chat, the bot:

1. **Polls** Teams for new messages containing the trigger
2. **Dispatches** the message to Claude for intent classification and processing
3. **Executes** the requested task via Claude Code worker sessions
4. **Replies** with results back to Teams

This is an internal NVIDIA tool for engineering teams who need Claude Code execution capabilities within their Teams workflows.

## How It Works

The bot operates in a continuous cycle:

- **Poll**: Every N seconds, query Teams chat history for messages containing `@niuma`
- **Dispatch**: Send triggering message to Claude for analysis; determine if user wants a new session, resume existing, or get information
- **Worker**: Launch Claude Code session with appropriate model and working directory if needed
- **Reply**: Stream results back to Teams or provide session status/links

## Prerequisites

- **Python 3.9+**
- **teams-cli**: Authenticated via `teams-cli auth login`
- **claude CLI**: Authenticated via `claude auth login`
- Access to Teams chats where the bot will run
- Claude API account with model access

## Installation

Clone the repository and install in development mode:

```bash
git clone <repository-url>
cd cyber_teams_niuma
pip install -e ".[dev]"
```

This installs niuma-bot with all development dependencies for testing.

## Configuration

### Setup

Create the configuration directory and copy the example config:

```bash
mkdir -p ~/.niuma
cp config.yaml.example ~/.niuma/config.yaml
```

### Get Chat ID

To find your Teams chat ID, use:

```bash
teams-cli chat list --json
```

Look for the chat you want to monitor and copy the `id` field (format: `19:xxxxx@thread.v2`).

### Edit Configuration

Open `~/.niuma/config.yaml` and update:

- **teams.chat_ids**: Add your chat IDs from the list above
- **security.allowed_users**: Add email addresses of users who can trigger the bot
- **security.admin_users**: Add email addresses of admin users (can list all sessions, stop others)
- **claude.dispatcher_model**: Model for intent classification (default: `sonnet`)
- **claude.worker_model**: Model for executing tasks (default: `sonnet`)
- **storage.db_path**: Path to SQLite database (default: `~/.niuma/niuma.db`)

Example minimal config:

```yaml
teams:
  chat_ids:
    - "19:abc123@thread.v2"
  trigger: "@niuma"
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
  db_path: "~/.niuma/niuma.db"
```

## Running

### Foreground

Start the bot and watch logs in the current terminal:

```bash
niuma
```

### Daemon Mode

Run in the background (similar to nohup):

```bash
niuma --daemon
```

Logs are written to `~/.niuma/niuma.log`.

### Custom Config Path

Specify a non-default config file:

```bash
niuma -c /path/to/config.yaml
```

## Usage in Teams

Once running, use the bot in Teams by mentioning `@niuma` followed by your request. The bot supports the following commands:

| Command | Example | Behavior |
|---------|---------|----------|
| **New Session** | `@niuma create a Python script that prints "hello world"` | Starts a new Claude Code session with your request |
| **Resume Session** | `@niuma continue <session-id>` | Resumes a previous session with a new prompt |
| **List Sessions** | `@niuma list` | Shows active sessions (admins see all, others see only theirs) |
| **Session Status** | `@niuma status <session-id>` | Gets current status of a specific session |
| **Stop Session** | `@niuma stop <session-id>` | Stops a running session (owners and admins only) |
| **Quick Reply** | `@niuma what is 2+2?` | Answers simple questions directly (no session created) |

The dispatcher analyzes each message and determines the appropriate action. Session results are posted back to the chat when complete.

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This includes pytest, pytest-asyncio, and pytest-cov.

### Run Tests

Execute the full test suite with coverage:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_poller.py
```

Check coverage:

```bash
pytest --cov=src/niuma --cov-report=term-missing
```

### Project Structure

- `src/niuma/` - Core modules
  - `main.py` - CLI entry point and bot orchestration
  - `poller.py` - Teams chat polling and message parsing
  - `dispatcher.py` - Intent classification via Claude
  - `session.py` - Claude Code session management
  - `responder.py` - Sending messages back to Teams
  - `config.py` - Configuration loading and validation
  - `db.py` - SQLite database for state tracking
- `tests/` - Test suite with unit and integration tests
- `config.yaml.example` - Example configuration

## Troubleshooting

**Bot not starting**: Check `~/.niuma/niuma.log` for errors. Ensure config.yaml is valid YAML and all paths are correct.

**Messages not being detected**: Verify the chat ID is correct and the bot has access to the chat. Check that allowed_users includes the sender's email.

**teams-cli auth expired**: Run `teams-cli auth login` to refresh authentication.

**claude CLI auth expired**: Run `claude auth login` to refresh authentication.

**Sessions timing out**: Check that claude CLI is working: `claude --version`. Increase `session_timeout` in config if needed (default: 86400 seconds = 24 hours).
