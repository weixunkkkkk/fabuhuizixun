#!/bin/zsh
cd "$(dirname "$0")"

REMOTE="$(git remote get-url origin 2>/dev/null)"
if [ -z "$REMOTE" ]; then
  REMOTE="https://github.com/weixunkkkkk/fabuhuizixun.git"
  git remote add origin "$REMOTE" 2>/dev/null || true
fi
export LAUNCH_FEED_GIT_REMOTE="$REMOTE"
export LAUNCH_FEED_GIT_BRANCH="main"

./修复GitHub连接.command
if [ "$?" -ne 0 ]; then
  echo ""
  echo "GitHub 连接不可用，已停止。请打开代理/VPN 后重新双击。"
  echo ""
  read "?按回车关闭这个窗口..."
  exit 1
fi
if [ -f ".codex_proxy_env" ]; then
  source ".codex_proxy_env"
fi

echo "开始刷新并上传发布会订阅源。"
echo "输出文件：out/subscription_feed.ics"
echo "GitHub 仓库：https://github.com/weixunkkkkk/fabuhuizixun"
echo ""

python3 run_daily_upload_github.py
code=$?

echo ""
if [ "$code" -eq 0 ]; then
  echo "完成。"
  echo ""
  echo "GitHub Pages 订阅链接："
  echo "https://weixunkkkkk.github.io/fabuhuizixun/out/subscription_feed.ics"
else
  echo "失败，返回码：$code"
  echo "请查看 logs/daily_github_upload.log 或直接把终端输出发给我。"
fi

echo ""
read "?按回车关闭这个窗口..."
