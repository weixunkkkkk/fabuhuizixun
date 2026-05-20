#!/bin/zsh
set -u

export HOME="/Users/mac"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

PROJECT="/Users/mac/Documents/New project/launch-calendar-bot"
LOG_DIR="$PROJECT/logs"
LOG="$LOG_DIR/daily_github_upload.log"

mkdir -p "$LOG_DIR"
cd "$PROJECT" || exit 1

{
  echo ""
  echo "==== $(date '+%Y-%m-%d %H:%M:%S %Z') ===="
  /usr/bin/python3 run_daily_upload_github.py
  code=$?
  echo "exit=$code"
} >> "$LOG" 2>&1

exit "$code"
