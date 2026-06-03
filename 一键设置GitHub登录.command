#!/bin/zsh
cd "$(dirname "$0")"

echo "你不想输入 Token，所以改用 SSH 公钥登录。"
echo "这个方式会打开 GitHub 网页，你可以在网页里输入密码确认。"
echo ""

./一键设置SSH并上传GitHub.command
