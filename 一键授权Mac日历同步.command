#!/bin/zsh
cd "$(dirname "$0")"

echo "正在请求 Mac 日历权限..."
CLANG_MODULE_CACHE_PATH=".swift-module-cache" swift mac_calendar_sync.swift --authorize-only --calendar-name "科技新品发布会日程"

echo ""
echo "如果系统弹出日历权限，请点允许。授权完成后，每天自动任务会同步到 Mac 日历。"
echo ""
read "?按回车关闭这个窗口..."
