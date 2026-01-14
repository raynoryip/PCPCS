#!/bin/bash
# PCPCS macOS Build Script
# 此腳本會將 PCPCS 打包成 .app 應用程式

echo "============================================"
echo "  PCPCS macOS Build Script"
echo "============================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found! Please install Python 3.7+"
    echo "  brew install python3"
    exit 1
fi

# 進入專案目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# 建立虛擬環境（如果不存在）
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
echo "[INFO] Installing dependencies..."
pip install --upgrade pip
pip install pyinstaller pillow

# 打包成 .app
echo "[INFO] Building PCPCS.app..."
pyinstaller --noconfirm --onefile --windowed \
    --name "PCPCS" \
    --add-data "assets:assets" \
    --hidden-import "PIL" \
    --hidden-import "PIL.Image" \
    --hidden-import "PIL.ImageTk" \
    --osx-bundle-identifier "com.perspic.pcpcs" \
    main.py

# 檢查結果
if [ -d "dist/PCPCS.app" ] || [ -f "dist/PCPCS" ]; then
    echo ""
    echo "============================================"
    echo "  Build Success!"
    echo "  Output: dist/PCPCS.app (or dist/PCPCS)"
    echo "============================================"
else
    echo ""
    echo "[ERROR] Build failed!"
    exit 1
fi
