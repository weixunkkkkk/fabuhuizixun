#!/bin/zsh
set -u

cd "$(dirname "$0")"

REMOTE="https://github.com/weixunkkkkk/fabuhuizixun.git"
export LAUNCH_FEED_GIT_REMOTE="$REMOTE"
export LAUNCH_FEED_GIT_BRANCH="main"

git remote set-url origin "$REMOTE" 2>/dev/null || true

echo "准备配置 GitHub HTTPS Token 登录。"
echo ""
echo "GitHub 现在不支持用账号密码推送代码。"
echo "你需要使用 Personal Access Token。"
echo ""
echo "Token 要求："
echo "- Fine-grained token：选择 weixunkkkkk/fabuhuizixun，Contents 权限选 Read and write"
echo "- Classic token：勾选 repo"
echo ""
echo "创建 Token 页面："
echo "https://github.com/settings/tokens"
echo ""
open "https://github.com/settings/tokens" >/dev/null 2>&1 || true

./修复GitHub连接.command
if [ "$?" -ne 0 ]; then
  echo ""
  echo "GitHub 网络连接不可用。请先打开代理/VPN 后重新运行。"
  echo ""
  read "?按回车关闭这个窗口..."
  exit 1
fi

echo ""
read "GITHUB_USER?请输入 GitHub 用户名（通常是 weixunkkkkk）："
if [ -z "$GITHUB_USER" ]; then
  GITHUB_USER="weixunkkkkk"
fi

echo "请粘贴 GitHub Token。输入时不会显示，这是正常的。"
read -rs "GITHUB_TOKEN?GitHub Token："
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
  echo "Token 为空，已停止。"
  read "?按回车关闭这个窗口..."
  exit 1
fi

printf "protocol=https\nhost=github.com\n\n" | git credential reject >/dev/null 2>&1 || true
printf "protocol=https\nhost=github.com\nusername=%s\npassword=%s\n\n" "$GITHUB_USER" "$GITHUB_TOKEN" | git credential approve

unset GITHUB_TOKEN

echo ""
echo "正在测试 GitHub 登录..."
if ! git ls-remote --heads origin main >/dev/null 2>&1; then
  echo "登录测试失败。请确认 Token 权限包含仓库 Contents: Read and write。"
  read "?按回车关闭这个窗口..."
  exit 1
fi

echo "登录测试通过，开始上传当前提交..."
git push -u origin HEAD:main
code=$?

echo ""
if [ "$code" -eq 0 ]; then
  echo "上传完成。"
  echo "GitHub Pages 订阅链接："
  echo "https://weixunkkkkk.github.io/fabuhuizixun/out/subscription_feed.ics"
else
  echo "上传失败，返回码：$code"
fi

echo ""
read "?按回车关闭这个窗口..."
