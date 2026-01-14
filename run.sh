#!/bin/bash
# PCPCS 啟動腳本 (Linux/macOS)

cd "$(dirname "$0")"

# 檢查 Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "錯誤: 找不到 Python"
    echo "請安裝 Python 3.7 或更高版本"
    exit 1
fi

echo "使用 $PYTHON 啟動 PCPCS..."
$PYTHON main.py
