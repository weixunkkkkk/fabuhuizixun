#!/bin/zsh
cd "$(dirname "$0")"

echo "正在刷新发布会清单..."
if [ -f "config.json" ]; then
  python3 launch_calendar.py --config config.json
else
  python3 launch_calendar.py --config config.example.json
fi

echo ""
echo "正在打开清单页面..."
open out/events.html
