# PCPCS - Perspic Cross PC Communication System

**Version 1.0.0**

[English](#english) | [繁體中文](#繁體中文)

---

## English

A cross-platform P2P LAN communication tool that enables real-time text and file transfer between Linux, Windows, and macOS.

### Features

- **Auto Discovery** - UDP broadcast automatically finds other PCPCS nodes on your local network
- **Ping Test** - Automatically tests connection status and displays latency
- **Text Transfer** - Real-time text transmission with auto-copy to clipboard on receive
- **File Transfer** - Supports files of any size with progress bar display
- **Folder Transfer** - Send entire folders with per-file progress, resume support for interrupted transfers, and automatic skip for identical files
- **Cross-Platform** - Works on Linux/Windows/macOS without installation
- **Bilingual UI** - Supports Traditional Chinese and English interface
- **No Dependencies** - Uses only Python standard library (no pip install required)

### Requirements

- Python 3.7+
- tkinter (may need separate installation on Linux)

### Installing tkinter

**Ubuntu/Debian:**
```bash
sudo apt install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
```bash
brew install python-tk
```

**Windows:** tkinter is included with Python

### How to Run

**Linux / macOS:**
```bash
./run.sh
# or
python3 main.py
```

**Windows:**
```
Double-click run.bat
# or
python main.py
```

### Building Standalone Executable

To package PCPCS as a standalone executable (no Python required for end users):

```bash
# Install PyInstaller
pip install pyinstaller

# Run the build script
python build.py
```

The executable will be created in the `dist/` folder.

### Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 52525 | UDP | Node Discovery |
| 52526 | TCP | File/Text Transfer |

Make sure your firewall allows these two ports.

### Received Files Location

Received files are saved to: `~/PCPCS_Received/`

### Screenshot

The GUI displays:
- Left panel: Discovered computers list and recent connections
- Right panel: Chat conversation, file selector, and system log
- Bottom: Transfer progress and copyright info

---

## 繁體中文

跨平台 P2P 區域網路通訊工具，支援 Linux、Windows 與 macOS 之間即時傳輸文字和檔案。

### 功能

- **自動發現** - UDP 廣播自動找到區網內的其他 PCPCS 節點
- **Ping 測試** - 自動測試連接狀態，顯示延遲時間
- **文字傳輸** - 即時傳輸文字，接收後自動複製到剪貼簿
- **檔案傳輸** - 支援任意大小檔案，有進度條顯示
- **資料夾傳輸** - 發送整個資料夾，支援逐檔案進度顯示、中斷續傳、自動跳過相同檔案
- **跨平台** - Linux/Windows/macOS 都能運行，無需安裝
- **雙語介面** - 支援繁體中文和英文介面
- **無依賴** - 只使用 Python 標準庫（無需 pip install）

### 需求

- Python 3.7+
- tkinter (Linux 可能需額外安裝)

### 安裝 tkinter

**Ubuntu/Debian:**
```bash
sudo apt install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
```bash
brew install python-tk
```

**Windows:** Python 已內建 tkinter

### 使用方式

**Linux / macOS:**
```bash
./run.sh
# 或
python3 main.py
```

**Windows:**
```
雙擊 run.bat
# 或
python main.py
```

### 打包成獨立執行檔

如需打包 PCPCS 成獨立執行檔（用戶無需安裝 Python）：

```bash
# 安裝 PyInstaller
pip install pyinstaller

# 執行打包腳本
python build.py
```

打包後的檔案會在 `dist/` 目錄。

### 端口

| 端口 | 協定 | 用途 |
|------|------|------|
| 52525 | UDP | 節點發現 |
| 52526 | TCP | 檔案/文字傳輸 |

請確保防火牆允許這兩個端口。

### 接收檔案位置

接收的檔案儲存在: `~/PCPCS_Received/`

### 截圖

GUI 介面包含：
- 左側面板：已發現的電腦列表和最近連線
- 右側面板：對話視窗、檔案選擇器和系統日誌
- 底部：傳輸進度和版權資訊

---

**© 2025 Perspic AI Engineering Limited**

Website: [perspic.net](https://perspic.net)
