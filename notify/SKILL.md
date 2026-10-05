---
name: notify
description: Post a short message to the team's Discord channel (#nightly-plan on the UpStock server) through a webhook. Used by the trading nightly plan (--notify), and directly when the user says "ping us", "send it to Discord", "notify the channel", or wants a summary pushed to both phones. Send-only; it cannot read the channel.
---

# Notify (Discord webhook)

**Send-only.** A webhook can post into one channel. It cannot read messages, see members or act as the user.

## Use
- From Python: load `notify/notify.py` and call `send(title, lines, color)`. It returns True or False and never raises.
- From the shell: `python3 notify/notify.py "Title" "line 1" "line 2" --color 0f6b4f`
- Colors: `GREEN` (buy / good news), `ORANGE` (exit / attention), `GREY` (info / nothing to do).

## Rules
- The webhook URL is a secret. It lives only in env var `DISCORD_WEBHOOK_URL`, set in the user's own shell profile. Never print it, paste it in chat, or commit it. If it leaks, delete the webhook in Discord (channel settings > Integrations > Webhooks) and create a new one.
- Keep messages short: a title and a few lines. Link to or name the full report rather than pasting it.
- Never say or imply that an order was placed. Trading messages should end with "Analysis only, nothing was ordered."
- Sending to the channel is an outward action. Send when the user asks or a script's `--notify` flag is set, not on your own initiative.

## Install
Copy this folder next to `trading/` (`cp -r trading notify ~/.claude/skills/`). The nightly plan finds it at `../notify/notify.py` relative to `trading/`.
