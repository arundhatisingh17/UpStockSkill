"""Shared module: post a message to the team Discord channel. Send-only; knows nothing about trading.

Usage:
  import:  send("Title", ["line 1", "line 2"], color=0x0F6B4F)
  CLI:     python3 notify.py "Title" "line 1" "line 2" [--color 0f6b4f]

Webhook comes from env var DISCORD_WEBHOOK_URL (set it in your shell profile; never commit or paste it).
Never raises: a failed notification must not break the caller.
"""
import argparse
import json
import os
import urllib.request

GREEN, ORANGE, GREY = 0x0F6B4F, 0xA2461C, 0x6B6B63


def send(title, lines, color=GREY):
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        print("notify: DISCORD_WEBHOOK_URL not set, skipped")
        return False
    payload = {"embeds": [{"title": title[:256], "description": "\n".join(lines)[:4000], "color": color}]}
    # Discord's edge rejects urllib's default User-Agent, so send our own
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "UpStockSkill-notify/1.0"})
    try:
        urllib.request.urlopen(req, timeout=10)
        print("notify: sent")
        return True
    except Exception as e:
        print("notify: failed:", e)
        return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("lines", nargs="*")
    ap.add_argument("--color", default="6b6b63", help="hex, e.g. 0f6b4f")
    a = ap.parse_args()
    send(a.title, a.lines, int(a.color, 16))
