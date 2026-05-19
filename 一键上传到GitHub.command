#!/bin/zsh
cd "$(dirname "$0")"

echo "正在上传到 GitHub: https://github.com/weixunkkkkk/fabuhui"
echo ""

GIT_DIR=".git-local" GIT_WORK_TREE="." git push -u origin main
code=$?

echo ""
if [ "$code" -eq 0 ]; then
  echo "上传完成。"
  echo ""
  echo "GitHub Pages 订阅链接："
  echo "https://weixunkkkkk.github.io/fabuhui/out/subscription_feed.ics"
  echo ""
  echo "如果还没开启 Pages，请到仓库 Settings -> Pages，选择 main / root。"
else
  echo "上传失败。请确认你有 weixunkkkkk/fabuhui 的写入权限，并已在本机登录 GitHub。"
fi

echo ""
read "?按回车关闭这个窗口..."
