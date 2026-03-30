---
name: managing-teams
description: "Manage Microsoft Teams chats and channels via teams-cli. Send and read chat messages, browse channels, manage chat members. Use when sending Teams messages, reading chat history, or managing group chat membership."
---

# Teams Chat & Channel Management

Manage Microsoft Teams chats and channels via `teams-cli`.

## Verify Installation

```bash
teams-cli --version
```

If command not found, see [installation page](https://outlook-cli-80d21a.gitlab-master-pages.nvidia.com/).

## Quick Start

```bash
teams-cli auth login          # One-time setup (shared with outlook-cli, calendar-cli)
teams-cli chat list --json    # List recent chats
teams-cli chat read <id>      # Read messages from a chat
teams-cli chat send <id> --body "Hello!"
```

Run `teams-cli --help` or `teams-cli <command> --help` for full syntax, flags, and examples.

## Features

- **Chats**: List, read, send, and reply to messages in 1:1 and group chats
- **Members**: List, add, and remove members in group chats
- **Teams**: List teams you're a member of
- **Channels**: List channels, read channel messages
- **Output**: JSON, TOON, and human-readable formats

## Workflows

*Run `teams-cli <command> --help` for detailed command workflows.*

## Troubleshooting

- **Auth errors**: Run `teams-cli auth login` to re-authenticate
- **Permission denied on member operations**: `ChatMember.ReadWrite` scope is required; verify with `teams-cli auth status`
- **Cannot add members to 1:1 chats**: Member management only works on group chats

## Related

- [authenticating-entra-device-code](../authenticating-entra-device-code/SKILL.md) for auth setup
