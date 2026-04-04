Now I have a thorough understanding of the architecture. Let me compile the analysis.

---

# J-Bot Architecture Analysis

## 1. Current Architecture Overview

J-Bot is a **poll-based Teams chatbot** that uses Claude Code as its AI backend. The Python package is named `niuma` (internal name), entry point at `src/niuma/main.py`.

### Component Map

```
NiumaBot (main.py)          -- Top-level orchestrator, owns the poll loop
  |
  +-- Poller (poller.py)    -- Fetches Teams messages via Graph API
  +-- Manager (manager.py)  -- Single persistent Claude Code session (the "brain")
  +-- SessionManager (session.py)  -- Manages worker Claude Code subprocesses
  +-- Responder (responder.py)     -- Sends formatted HTML messages to Teams
  +-- Database (db.py)             -- SQLite (aiosqlite) for all state
  +-- TeamsAPI (teams_api.py)      -- Graph API client (token refresh, send/poll)

Scripts (shell):
  jbot-send.sh        -- Graph API message sender (used by Manager + Workers)
  jbot-worker.sh      -- Creates session chat + launches background worker
  jbot-worker-run.sh  -- Actual Claude Code invocation for workers
  jbot-draft.sh       -- Create Outlook draft
  jbot-email.sh       -- Send email
  jbot-calendar.sh    -- Create calendar event
```

### Execution Model

There are **two distinct execution paths** for workers:

**Path A: Python-managed workers** (`SessionManager.start_session` / `resume_session`)
- Workers run as `asyncio.create_subprocess_exec` inside the Python process
- Tracked in `self._active` dict
- Watched by `watcher.py` polling the DB for completion
- Used when the Python poll loop creates sessions directly

**Path B: Shell-managed workers** (`jbot-worker.sh`)
- Manager Claude session calls `jbot-worker.sh` via bash tool
- Creates Teams group chat, registers session in DB via direct SQLite
- Launches `jbot-worker-run.sh` via `nohup` in background
- Completely decoupled from the Python process
- Worker updates DB status itself when done

This duality is a key architectural characteristic -- the Manager (a Claude Code session with tool access) can spawn workers through shell scripts that bypass the Python orchestrator entirely.

### Data Flow

```
Teams Chat
    |
    v
[Poller] --poll every 5-60s via Graph API--> [TeamsMessage objects]
    |
    v
[NiumaBot.poll_once] -- routes by chat type:
    |
    +-- Trigger chats: filter for "@jbot" prefix -> _handle_message
    +-- Manager chat: all messages go direct -> _handle_message  
    +-- Session chats: auto-route to bound session -> resume_session
    |
    v
[Handler] -- sends to Manager Claude session (--resume or fresh)
    |
    v
[Manager Claude Code] -- has tools: jbot-send.sh, jbot-worker.sh, sqlite3
    |
    +-- Simple questions: replies directly via jbot-send.sh
    +-- Complex tasks: calls jbot-worker.sh -> background worker
    |
    v
[Worker] -- reports to its own Teams chat via jbot-send.sh
    |
    v
[Watcher] -- polls DB, feeds result back to Manager on completion
```

## 2. Polling and Dispatch

### Polling Mechanism

- **Adaptive interval**: Starts at 5 seconds, ramps up to `config.teams.poll_interval` (default 60s) after 3 idle cycles
- **Hard timeout**: Each `poll_once` cycle has a 60-second `asyncio.wait_for` timeout
- **Three chat types polled** per cycle:
  1. **Trigger chats** (from config + DB `watched_chats`) -- require trigger prefix like "@jbot"
  2. **Manager chat** (single dedicated group chat) -- no trigger needed
  3. **Session chats** (all chats with `session_chat_id` in DB) -- auto-route to bound session
- **Deduplication**: `poll_state` table stores `last_message_id` per chat. Integer comparison for message ordering.
- **Backoff**: Per-chat exponential backoff on network errors (doubles up to 300s). Rate limit (HTTP 429) triggers 30s sleep.

### Message Routing

1. **Trigger chats**: Messages must start with the trigger prefix (e.g., "@jbot"). After stripping the prefix, the prompt goes to `_handle_message`.
2. **Manager chat**: All non-bot messages go directly to `_handle_message`. No trigger required.
3. **Session chats**: Messages auto-route to the bound worker session via `resume_session`. If worker is busy, messages are queued in the DB.

### Dispatch Logic

The `handler.py` module sends every message to `Manager.process()`. The Manager Claude session decides whether to:
- Reply directly (greetings, simple questions, DB queries)
- Dispatch via `jbot-worker.sh` (code tasks, analysis, complex work)

The Manager is instructed in its system prompt to be a DISPATCHER -- it should not write code itself.

## 3. Session Lifecycle

### Creation

Two paths:

**Python path** (used for session-chat routed messages):
1. `SessionManager.start_session()` -> generates short ID (MMDD-XXXX), inserts into DB
2. Launches `claude -p <prompt>` subprocess with `--name jbot-<user>-<sid>`
3. Returns immediately; `_wait_for_completion` task watches the subprocess

**Shell path** (used by Manager dispatching):
1. `jbot-worker.sh` generates session ID, creates Teams group chat via Graph API
2. Registers session directly in SQLite (bypasses Python `Database` class)
3. Launches `jbot-worker-run.sh` via `nohup &` -- fully detached from Python process
4. Worker runs `claude -p <task>` with `--append-system-prompt` containing chat_id for reporting

### Resume

- `SessionManager.resume_session()` uses `--resume <claude_session_id>` to continue a previous conversation
- Per-session `asyncio.Lock` prevents concurrent resumes
- If Claude session expired ("No conversation found"), falls back to fresh start with original prompt
- Session chats auto-queue messages if worker is busy, then auto-resume after completion

### Monitoring

**Watcher** (`watcher.py`):
- Polls DB every 2 seconds for session status changes
- Sends heartbeat messages every 60 seconds to the Teams chat
- Reads Claude JSONL files (`~/.claude/projects/*/UUID.jsonl`) for real-time progress
- Falls back to searching by session name pattern if no JSONL match
- On completion: sends result to Teams, feeds summary back to Manager via `feed_worker_result`

**Shell workers**: Self-monitor. `jbot-worker-run.sh` updates DB status and sends completion messages to both session chat and manager chat.

### Stopping

- `SessionManager.stop_session()` kills the subprocess (`proc.kill()`)
- Graceful shutdown: `NiumaBot.shutdown()` waits 30 seconds for background tasks, then cancels
- Shell workers: orphaned if Python process dies (they are `nohup` detached)

## 4. Manager Session

The Manager is a **single persistent Claude Code session** that gets `--resume`d for every incoming message. Key properties:

- **Session ID persistence**: Stored in `bot_state` table (`manager_session_id` key). Survives bot restarts.
- **System prompt**: Injected via `--append-system-prompt` on first creation. Contains instructions for using `jbot-send.sh`, `jbot-worker.sh`, `sqlite3`, and decision logic.
- **Direct Teams replies**: Manager calls `jbot-send.sh` as a tool during execution. No JSON parsing needed.
- **30-minute timeout**: If Manager takes longer, the poll loop releases but the Claude process continues in background.
- **Auto-recovery**: If session expired, creates a fresh session on next message.
- **Context accumulation**: Each `--resume` adds to the conversation, so the Manager remembers all prior interactions.

### Manager-Worker Communication

- **Manager to Worker**: Manager calls `jbot-worker.sh` which creates the worker and its dedicated chat
- **Worker to Manager**: Indirect. Watcher detects completion in DB, calls `Manager.feed_worker_result()` which resumes the Manager session with a `[WORKER RESULT]` context block
- **Shared state**: SQLite `sessions` table is the shared truth. Both Manager (via sqlite3 tool) and Workers (via direct SQLite in shell scripts) read/write it.

## 5. Teams Integration

### Authentication

- Shared OAuth token cache at `~/.ai-pim-utils/token-cache-ai-pim-utils`
- Write-capable client (`29c0325f` -- Microsoft "Office Desktop") preferred for send operations
- Automatic token refresh using stored refresh token
- Thread-safe in-memory token caching with RLock

### Message Sending

Two mechanisms:
1. **Python `Responder`**: Uses `teams_api.send_chat_message_async()` for bot-initiated messages (acks, heartbeats, results)
2. **Shell `jbot-send.sh`**: Used by Manager and Workers (Claude Code tool calls). Imports `niuma.teams_api` Python module.

Both append a `<hr/><p><em>Sent by J-Bot</em></p>` footer for bot-message detection during polling.

### Chat Management

- Manager chat: Created once on startup, persisted in `bot_state` table
- Session chats: Created per-worker via `create_session_chat` (Graph API group chat creation)
- Watched chats: Dynamic list in `watched_chats` table, added at runtime

## 6. Current Limitations

### A. Manager is NOT Persistent (Always-On)

The Manager session is **reactive only**. It is invoked (resumed) when a message arrives, runs, and exits. Between messages, there is no Manager process running. The Manager cannot:
- Self-poll for periodic tasks
- Monitor worker health proactively
- Execute scheduled operations
- Maintain real-time awareness

The TODO comment in `main.py` line 27 confirms this is a known gap: `# TODO (multi-manager): Add config option for per-directory managers`.

### B. Cross-Project Worker Visibility is Fragile

Workers spawned via `jbot-worker.sh` run in arbitrary CWDs across different project directories. The DB tracks `cwd` per session, but:
- The Python `SessionManager._active` dict only knows about Python-spawned workers
- Shell-spawned workers are invisible to the Python process after launch
- No process-level health checks for shell workers (only DB status)
- If a shell worker crashes without updating DB, it appears permanently "running"

### C. Dual Worker Path Creates Inconsistency

**Python-managed workers** (SessionManager):
- Tracked in `_active` dict
- Watched by `watcher.py`
- Auto-retry on transient errors
- Auto-resume with queued messages

**Shell-managed workers** (jbot-worker.sh):
- Fire-and-forget from Python's perspective
- Self-report to DB
- No retry logic
- No queue processing

This means features like message queuing and auto-retry only work for Python-path workers.

### D. Single-Point-of-Failure Polling

- One Python process does ALL polling. If it crashes, everything stops.
- No watchdog (the `jbot-watchdog.sh` file does not exist)
- The `_daemonize` option is a simple double-fork with no supervision
- Shell workers survive crashes, but new messages stop being processed

### E. Manager Context Bloat

Every message and worker result is fed into the Manager's conversation history via `--resume`. Over time:
- Context window fills up
- Response latency increases
- Eventually the session must be reset, losing all accumulated context

### F. No Worker Status API

Workers cannot query their own status or communicate with sibling workers. Each worker is isolated with:
- Its own Claude session
- Its own Teams chat
- Read-only access to the shared SQLite DB (via sqlite3 tool)

There is no pub/sub or event system for inter-worker coordination.

### G. Session Chat Polling is Unbounded

`list_session_chat_ids()` returns ALL session chat IDs ever created (including completed/expired sessions). Each one gets polled every cycle, creating O(n) API calls where n grows monotonically. The `cleanup_expired_sessions` method marks old sessions as expired but does not remove their `session_chat_id` from the result set.

### H. Bot Message Detection is Brittle

Bot messages are detected by checking for string fragments ("Sent by J-Bot", "ai-pim-utils", "Sent by niuma") in `body_raw`. This is fragile and could break if:
- Message format changes
- Another bot uses similar text
- HTML encoding varies

## 7. Key Files Summary

| File | Lines | Role |
|------|-------|------|
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/main.py` | 673 | Top-level bot class, poll loop, lifecycle |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/manager.py` | 375 | Manager Claude session, prompt building |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/session.py` | 359 | Worker session lifecycle (Python path) |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/poller.py` | 188 | Graph API polling, message parsing |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/handler.py` | 112 | Message routing, role checks |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/watcher.py` | 240 | Session completion monitoring, JSONL progress |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/db.py` | 430 | SQLite schema, CRUD, migrations |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/responder.py` | 139 | HTML formatting, Teams message sending |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/teams_api.py` | 428 | Graph API client, OAuth token management |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/src/niuma/config.py` | 147 | YAML config loading, dataclass models |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/scripts/jbot-worker.sh` | 96 | Worker launcher (creates chat + DB entry) |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/scripts/jbot-worker-run.sh` | 153 | Worker execution (Claude Code invocation) |
| `/home/scratch.jackeyw_mobile_1/J-Bot-Everyone-s-Jarvis-/scripts/jbot-send.sh` | 41 | Graph API message sender |

## 8. Architecture Diagram

```
                    Microsoft Teams (Graph API)
                         |          ^
                   poll  |          |  send (jbot-send.sh / teams_api.py)
                         v          |
                 +-------------------+
                 |    NiumaBot       |
                 |  (main.py)        |
                 |                   |
                 | poll_once() loop  |
                 | 5s-60s adaptive   |
                 +---+-------+-------+
                     |       |
          +----------+       +----------+
          v                             v
   +------------+              +----------------+
   |  Manager   |              | SessionManager |
   | (Claude CC |              | (Python-path   |
   |  session)  |              |  workers)      |
   |            |              |                |
   | --resume   |              | asyncio.create_|
   | per msg    |              | subprocess_exec|
   +-----+------+              +-------+--------+
         |                             |
         |  calls jbot-worker.sh       |  _wait_for_completion
         v                             v
   +------------+              +----------------+
   | Shell-path |              | In-process     |
   | Workers    |              | Workers        |
   | (nohup &)  |              | (asyncio.Task) |
   +-----+------+              +-------+--------+
         |                             |
         +--------+   +---------------+
                  v   v
            +------------+
            |  SQLite DB |  <-- shared state
            | ~/.jbot/   |
            | jbot.db    |
            +------------+
```

## 9. Observations for Your Goals

Regarding **persistent Manager**: The current Manager is invoked on-demand via `--resume`. Making it always-on would require either (a) keeping a long-running Claude Code interactive session, or (b) implementing a self-polling loop within the Manager's system prompt that calls itself on a timer. The 30-minute timeout on Manager calls already hints at the desire for longer-running Manager operations.

Regarding **cross-project worker management**: The DB already stores `cwd` per session and the CLAUDE.md documents project CWDs. The gap is that shell-spawned workers are fire-and-forget from Python's perspective. A unified worker registry with health checks (process existence verification) would close this gap.

Regarding **autonomous worker reporting**: Workers already report to their dedicated Teams chats via `jbot-send.sh`. The limitation is that they can only report to the chat they were told about at creation time. Allowing workers to discover and report to additional chats would require either (a) passing multiple chat IDs at launch, or (b) giving workers access to a "reporting registry" they can query.

Regarding **session management flexibility**: The dual Python/Shell worker paths create most of the friction. Unifying on a single path (likely the shell path, since it survives Python process restarts) with proper health monitoring would maximize flexibility.
