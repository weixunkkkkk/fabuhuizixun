#!/bin/zsh
cd "$(dirname "$0")"

echo "正在刷新发布会日历..."
if [ -f "config.json" ]; then
  python3 launch_calendar.py --config config.json
else
  python3 launch_calendar.py --config config.example.json
fi

echo ""
echo "正在打开日历导入文件..."
if [ -f "out/mac_calendar_import.ics" ]; then
  open out/mac_calendar_import.ics
else
  open out/launch_events.ics
fi

echo ""
echo "如果你的 Mac 日历已经登录 Google 账号，弹窗里选你的 Google 日历，然后点导入。"
echo "如果没有登录，先在 macOS 系统设置里把 Google 账号加到日历。"
echo ""
read "?按回车关闭这个窗口..."
