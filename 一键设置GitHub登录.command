#!/bin/zsh
cd "$(dirname "$0")"

echo "准备配置 GitHub 命令行登录。"
echo "你可以在打开的 GitHub 网页里继续用 Apple 账号登录，不需要输入 GitHub 密码。"
echo ""

if ! command -v gh >/dev/null 2>&1; then
  if ! command -v brew >/dev/null 2>&1; then
    echo "没有找到 Homebrew，无法自动安装 GitHub CLI。"
    echo "请先安装 Homebrew，或手动安装 GitHub CLI。"
    echo ""
    read "?按回车关闭这个窗口..."
    exit 1
  fi

  echo "正在安装 GitHub CLI（gh）..."
  brew install gh
  if [ "$?" -ne 0 ]; then
    echo "GitHub CLI 安装失败。"
    echo ""
    read "?按回车关闭这个窗口..."
    exit 1
  fi
fi

echo ""
echo "开始 GitHub 网页授权..."
gh auth status >/dev/null 2>&1
if [ "$?" -ne 0 ]; then
  gh auth login --hostname github.com --git-protocol https --web
fi

if [ "$?" -ne 0 ]; then
  echo "GitHub 授权未完成。"
  echo ""
  read "?按回车关闭这个窗口..."
  exit 1
fi

gh auth setup-git
GIT_DIR=".git-local" GIT_WORK_TREE="." git remote set-url origin https://github.com/weixunkkkkk/fabuhuizixun.git

echo ""
echo "检查上传脚本..."
python3 upload_subscription_feed_to_github.py --dry-run

echo ""
echo "配置完成。以后每天 9:30 自动化会上传 out/subscription_feed.ics。"
echo "GitHub Pages 订阅链接："
echo "https://weixunkkkkk.github.io/fabuhuizixun/out/subscription_feed.ics"
echo ""
read "?按回车关闭这个窗口..."
