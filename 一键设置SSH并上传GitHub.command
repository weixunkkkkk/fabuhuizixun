#!/bin/zsh
cd "$(dirname "$0")"

KEY="$HOME/.ssh/fabuhuizixun_ed25519"
PUB="$KEY.pub"
CONFIG="$HOME/.ssh/config"
REMOTE="git@github-fabuhuizixun:weixunkkkkk/fabuhuizixun.git"
export LAUNCH_FEED_GIT_REMOTE="$REMOTE"
export LAUNCH_FEED_GIT_BRANCH="main"

echo "准备配置 SSH 上传到 GitHub：weixunkkkkk/fabuhuizixun"
echo "这个方式不需要 GitHub CLI，也不需要在终端输入 GitHub 密码。"
echo ""

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ ! -f "$KEY" ]; then
  echo "正在生成专用 SSH key..."
  ssh-keygen -t ed25519 -C "fabuhuizixun-auto-upload" -f "$KEY" -N ""
  if [ "$?" -ne 0 ]; then
    echo "SSH key 生成失败。"
    read "?按回车关闭这个窗口..."
    exit 1
  fi
fi

chmod 600 "$KEY"
chmod 644 "$PUB"

if ! grep -q "Host github-fabuhuizixun" "$CONFIG" 2>/dev/null; then
  cat >> "$CONFIG" <<EOF

Host github-fabuhuizixun
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile $KEY
  IdentitiesOnly yes
  AddKeysToAgent yes
  UseKeychain yes
EOF
  chmod 600 "$CONFIG"
fi

pbcopy < "$PUB"
echo "SSH 公钥已经复制到剪贴板。"
echo ""
echo "接下来会打开 GitHub 添加 SSH key 页面。"
echo "在页面里："
echo "1. Title 可以填：fabuhuizixun-auto-upload"
echo "2. Key 里直接粘贴"
echo "3. 点 Add SSH key 保存"
echo ""
open "https://github.com/settings/ssh/new"
read "?保存好 SSH key 后，回到这里按回车继续..."

git remote set-url origin "$REMOTE" 2>/dev/null || git remote add origin "$REMOTE"

echo ""
echo "正在测试 SSH 连接..."
SSH_OUTPUT=$(ssh -o StrictHostKeyChecking=accept-new -T github-fabuhuizixun 2>&1)
echo "$SSH_OUTPUT"

if ! echo "$SSH_OUTPUT" | grep -q "successfully authenticated"; then
  echo ""
  echo "SSH 还没连通。请确认刚才已经把公钥添加到 GitHub。"
  echo "如果刚刚才保存，可以等 10 秒后重新运行这个脚本。"
  echo ""
  read "?按回车关闭这个窗口..."
  exit 1
fi

echo ""
echo "SSH 已连通，开始首次上传订阅源文件..."
./修复GitHub连接.command
if [ -f ".codex_proxy_env" ]; then
  source ".codex_proxy_env"
fi
python3 upload_subscription_feed_to_github.py
code=$?

echo ""
if [ "$code" -eq 0 ]; then
  echo "上传完成。以后每天 9:30 自动化会继续上传 out/subscription_feed.ics。"
  echo "GitHub Pages 订阅链接："
  echo "https://weixunkkkkk.github.io/fabuhuizixun/out/subscription_feed.ics"
else
  echo "上传失败。请确认你对 weixunkkkkk/fabuhuizixun 有写入权限。"
fi

echo ""
read "?按回车关闭这个窗口..."
