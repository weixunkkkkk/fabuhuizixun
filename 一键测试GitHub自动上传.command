#!/bin/zsh
cd "$(dirname "$0")"

echo "开始测试：刷新并上传 out/subscription_feed.ics"
echo ""

./daily_github_upload.sh
code=$?

echo ""
if [ "$code" -eq 0 ]; then
  echo "测试完成。"
  echo "GitHub Pages 订阅链接："
  echo "https://weixunkkkkk.github.io/fabuhuizixun/out/subscription_feed.ics"
else
  echo "测试失败，返回码：$code"
  echo "请查看 logs/daily_github_upload.log"
fi

echo ""
read "?按回车关闭这个窗口..."
