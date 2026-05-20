#!/bin/zsh
cd "$(dirname "$0")"

PROJECT="$(pwd)"
SCRIPT="$PROJECT/daily_github_upload.sh"
PLIST="$HOME/Library/LaunchAgents/com.weixunkkkkk.fabuhuizixun.feed.plist"
LABEL="com.weixunkkkkk.fabuhuizixun.feed"
LOG_DIR="$PROJECT/logs"

echo "准备安装 macOS 每日 9:30 自动上传任务。"
echo "它会每天刷新并上传：out/subscription_feed.ics"
echo ""

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"
chmod +x "$SCRIPT"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>$SCRIPT</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$PROJECT</string>

  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>30</integer>
  </dict>

  <key>StandardOutPath</key>
  <string>$LOG_DIR/launchagent.out.log</string>

  <key>StandardErrorPath</key>
  <string>$LOG_DIR/launchagent.err.log</string>

  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1
launchctl bootstrap "gui/$(id -u)" "$PLIST"
code=$?

echo ""
if [ "$code" -eq 0 ]; then
  launchctl enable "gui/$(id -u)/$LABEL" >/dev/null 2>&1
  echo "安装完成。"
  echo "每天 9:30 会自动运行：$SCRIPT"
  echo ""
  echo "日志文件："
  echo "$LOG_DIR/daily_github_upload.log"
else
  echo "安装失败，launchctl 返回：$code"
fi

echo ""
read "?按回车关闭这个窗口..."
