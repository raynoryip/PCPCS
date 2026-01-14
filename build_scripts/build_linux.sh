#!/bin/bash
# PCPCS Linux Build Script
# 此腳本會將 PCPCS 打包成單一可執行檔

echo "============================================"
echo "  PCPCS Linux Build Script"
echo "============================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found! Please install Python 3.7+"
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

# 檢查 tkinter
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[WARNING] tkinter not found. Please install:"
    echo "  Ubuntu/Debian: sudo apt install python3-tk"
    echo "  Fedora: sudo dnf install python3-tkinter"
    echo "  Arch: sudo pacman -S tk"
fi

# 打包
echo "[INFO] Building PCPCS..."
pyinstaller --noconfirm --onefile \
    --name "PCPCS" \
    --add-data "assets:assets" \
    --hidden-import "PIL" \
    --hidden-import "PIL.Image" \
    --hidden-import "PIL.ImageTk" \
    main.py

# 檢查結果
if [ -f "dist/PCPCS" ]; then
    chmod +x dist/PCPCS
    echo ""
    echo "============================================"
    echo "  Build Success!"
    echo "  Output: dist/PCPCS"
    echo "============================================"
else
    echo ""
    echo "[ERROR] Build failed!"
    exit 1
fi
