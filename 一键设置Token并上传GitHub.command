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
echo "- Fine-grained token：Repository access 选择 Only select repositories -> weixunkkkkk/fabuhuizixun"
echo "- Fine-grained token：Repository permissions 里的 Contents 权限选 Read and write"
echo "- Classic token：勾选 repo"
echo ""
echo "如果你刚才遇到 403，说明旧 Token 只有读权限或没有这个仓库的写权限。"
echo "重新运行本脚本并粘贴新 Token，会覆盖旧 Token。"
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
echo "正在测试 GitHub 读取权限..."
if ! git ls-remote --heads origin main >/dev/null 2>&1; then
  echo "读取测试失败。请确认 Token 属于正确账号，并能访问 weixunkkkkk/fabuhuizixun。"
  read "?按回车关闭这个窗口..."
  exit 1
fi

echo "读取测试通过，开始同步远端最新提交..."
git fetch origin main
if [ "$?" -ne 0 ]; then
  echo "拉取远端最新提交失败，已停止。"
  read "?按回车关闭这个窗口..."
  exit 1
fi

git rebase --autostash origin/main
if [ "$?" -ne 0 ]; then
  echo "自动接上远端最新提交失败。请把终端输出发给我。"
  read "?按回车关闭这个窗口..."
  exit 1
fi

echo "正在测试 GitHub 写入权限..."
if ! git push --dry-run -u origin HEAD:main >/dev/null 2>&1; then
  echo ""
  echo "写入权限测试失败。"
  echo "请重新创建 GitHub Token，并确保权限正确："
  echo "1. Fine-grained token：Repository access 选择 Only select repositories"
  echo "2. 勾选仓库：weixunkkkkk/fabuhuizixun"
  echo "3. Repository permissions -> Contents 选择 Read and write"
  echo "4. 或者 Classic token 勾选 repo"
  echo ""
  echo "创建好后重新运行本脚本，粘贴新的 Token。"
  read "?按回车关闭这个窗口..."
  exit 1
fi

echo "写入权限测试通过，开始上传当前提交..."
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
