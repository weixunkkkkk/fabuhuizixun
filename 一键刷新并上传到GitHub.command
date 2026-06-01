#!/bin/zsh
cd "$(dirname "$0")"

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
