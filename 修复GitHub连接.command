#!/bin/zsh
set -u

cd "$(dirname "$0")"

REMOTE="https://github.com/weixunkkkkk/fabuhuizixun.git"
export LAUNCH_FEED_GIT_REMOTE="$REMOTE"
export LAUNCH_FEED_GIT_BRANCH="main"

echo "检查 GitHub 连接..."
git remote set-url origin "$REMOTE" 2>/dev/null || true

test_github() {
  local label="$1"
  shift
  echo "测试：$label"
  if curl -fsSI --connect-timeout 8 --max-time 15 "$@" https://github.com >/dev/null 2>&1; then
    echo "可用：$label"
    return 0
  fi
  return 1
}

clear_git_proxy() {
  git config --global --unset-all http.https://github.com.proxy >/dev/null 2>&1 || true
  git config --global --unset-all https.https://github.com.proxy >/dev/null 2>&1 || true
  git config --global --unset-all http.proxy >/dev/null 2>&1 || true
  git config --global --unset-all https.proxy >/dev/null 2>&1 || true
}

set_git_proxy() {
  local proxy="$1"
  clear_git_proxy
  git config --global http.https://github.com.proxy "$proxy"
  git config --global https.https://github.com.proxy "$proxy"
  echo "已设置 GitHub Git 代理：$proxy"
}

if test_github "直连"; then
  clear_git_proxy
  echo "GitHub 可直连，已清理 Git 代理配置。"
  exit 0
fi

echo "直连不可用，开始尝试常见本地代理端口..."

for port in 7890 7897 7899 6152 6153 8080 1087 10809 20170; do
  proxy="http://127.0.0.1:$port"
  if test_github "$proxy" --proxy "$proxy"; then
    set_git_proxy "$proxy"
    exit 0
  fi
done

for port in 1080 1087 10808 10809 7890 7891; do
  proxy="socks5h://127.0.0.1:$port"
  if test_github "$proxy" --proxy "$proxy"; then
    set_git_proxy "$proxy"
    exit 0
  fi
done

echo ""
echo "没有找到可用的 GitHub 连接。"
echo "请先打开你的代理/VPN，并确认代理软件允许 Terminal 使用。"
echo "如果你知道代理地址，可以手动运行："
echo "git config --global http.https://github.com.proxy http://127.0.0.1:7890"
echo "git config --global https.https://github.com.proxy http://127.0.0.1:7890"
echo ""
exit 1
