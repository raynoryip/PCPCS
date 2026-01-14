#!/usr/bin/env python3
"""
PCPCS - Perspic Cross PC Communication System
跨平台 P2P 通訊系統

使用方式:
  Linux:   python3 main.py 或 ./run.sh
  Windows: python main.py 或 雙擊 run.bat

功能:
  - 自動發現區域網路內的其他 PCPCS 節點
  - P2P 文字傳輸
  - P2P 檔案傳輸
  - 連接狀態測試 (Ping)
"""
import sys
import os

# 確保模組路徑正確
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """檢查依賴"""
    try:
        import tkinter
        return True
    except ImportError:
        print("錯誤: 找不到 tkinter 模組")
        print()
        print("請安裝 tkinter:")
        print("  Ubuntu/Debian: sudo apt install python3-tk")
        print("  Fedora: sudo dnf install python3-tkinter")
        print("  Arch: sudo pacman -S tk")
        print("  Windows: tkinter 應該已經內建於 Python")
        return False

def main():
    """主程式入口"""
    print("=" * 50)
    print("  PCPCS - Perspic Cross PC Communication System")
    print("=" * 50)
    print()

    # 檢查 Python 版本
    if sys.version_info < (3, 7):
        print(f"錯誤: 需要 Python 3.7 或更高版本")
        print(f"目前版本: {sys.version}")
        sys.exit(1)

    # 檢查依賴
    if not check_dependencies():
        sys.exit(1)

    print(f"Python 版本: {sys.version}")
    print()
    print("正在啟動 GUI...")
    print()

    # 啟動 GUI
    from gui.app import main as gui_main
    gui_main()

if __name__ == "__main__":
    main()
