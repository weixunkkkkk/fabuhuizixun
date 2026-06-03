#!/bin/zsh
cd "$(dirname "$0")"

export LAUNCH_FEED_GIT_REMOTE="https://github.com/weixunkkkkk/fabuhuizixun.git"
export LAUNCH_FEED_GIT_BRANCH="main"
git remote set-url origin "$LAUNCH_FEED_GIT_REMOTE" 2>/dev/null || true

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

echo "正在上传订阅源到 GitHub: https://github.com/weixunkkkkk/fabuhuizixun"
echo "流程：先刷新 IT之家科技日历，再生成 out/subscription_feed.ics，最后上传。"
echo ""

python3 run_daily_upload_github.py
code=$?

echo ""
if [ "$code" -eq 0 ]; then
  echo "刷新并上传完成。"
  echo ""
  echo "GitHub Pages 订阅链接："
  echo "https://weixunkkkkk.github.io/fabuhuizixun/out/subscription_feed.ics"
  echo ""
  echo "如果还没开启 Pages，请到仓库 Settings -> Pages，选择 main / root。"
else
  echo "上传失败。请确认你有 weixunkkkkk/fabuhuizixun 的写入权限，并已在本机登录 GitHub。"
fi

echo ""
read "?按回车关闭这个窗口..."
