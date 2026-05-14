#!/usr/bin/env python3
"""
Manual AI log script for Antigravity sessions.
Usage:
    python scripts/log_antigravity.py
    python scripts/log_antigravity.py --summary "built login page"
    python scripts/log_antigravity.py --prompt "create a REST API for users"
    python scripts/log_antigravity.py --prompt "fix bug in auth" --summary "fixed JWT token expiry"
"""
import json
import os
import sys
import io
import subprocess
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# --- UTF-8 fix for Windows ---
if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

VN_TZ = timezone(timedelta(hours=7))


def git(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def get_conversation_id():
    """Try to find the current Antigravity conversation ID from brain directory."""
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if not brain_dir.exists():
        return ""
    # Get most recently modified conversation directory
    conversations = [d for d in brain_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if not conversations:
        return ""
    latest = max(conversations, key=lambda d: d.stat().st_mtime)
    return latest.name


def main():
    parser = argparse.ArgumentParser(
        description="Log Antigravity AI session to .ai-log/session.jsonl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Log session start
  python scripts/log_antigravity.py

  # Log a prompt you sent
  python scripts/log_antigravity.py --prompt "create login page with React"

  # Log with summary of what was done
  python scripts/log_antigravity.py --summary "implemented user authentication flow"

  # Log both prompt and summary
  python scripts/log_antigravity.py --prompt "fix the bug" --summary "fixed null pointer in auth middleware"

  # Log with custom event type
  python scripts/log_antigravity.py --event SessionEnd --summary "finished session"
        """
    )
    parser.add_argument("--prompt", "-p", default="", help="The prompt you sent to Antigravity")
    parser.add_argument("--summary", "-s", default="", help="Summary of what the AI did")
    parser.add_argument("--event", "-e", default="UserPromptSubmit",
                        choices=["SessionStart", "UserPromptSubmit", "ToolUse", "SessionEnd"],
                        help="Event type (default: UserPromptSubmit)")
    parser.add_argument("--model", "-m", default="", help="Model used (e.g. gemini-2.5-pro)")
    args = parser.parse_args()

    log_dir = Path(os.environ.get("AI_LOG_DIR", ".ai-log"))
    log_dir.mkdir(exist_ok=True)

    ts = datetime.now(VN_TZ).isoformat()
    conversation_id = get_conversation_id()

    entry = {
        "ts": ts,
        "tool": "antigravity",
        "event": args.event,
        "session_id": conversation_id,
        "model": args.model,
        "repo": git("git remote get-url origin").split("/")[-1].replace(".git", ""),
        "branch": git("git rev-parse --abbrev-ref HEAD"),
        "commit": git("git rev-parse --short HEAD"),
        "student": git("git config user.email"),
        "prompt": args.prompt[:1000] if args.prompt else "",
        "summary": args.summary[:500] if args.summary else "",
    }

    # Remove empty fields for cleaner output 
    entry = {k: v for k, v in entry.items() if v != "" and v is not None}

    log_file = log_dir / "session.jsonl"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"✅ Logged: [{args.event}] {args.prompt or args.summary or 'session event'}")
        print(f"   File: {log_file}")
    except Exception as e:
        print(f"❌ Error writing log: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()