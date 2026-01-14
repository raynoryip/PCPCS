# PCPCS - Perspic Cross PC Communication System

跨平台 P2P 區域網路通訊工具，支援 Linux 與 Windows 之間即時傳輸文字和檔案。

## 功能

- **自動發現** - UDP 廣播自動找到區網內的其他 PCPCS 節點
- **Ping 測試** - 自動測試連接狀態，顯示延遲時間
- **文字傳輸** - 即時傳輸文字，接收後自動複製到剪貼簿
- **檔案傳輸** - 支援任意大小檔案，有進度條顯示
- **跨平台** - Linux/Windows 都能運行，無需安裝

## 需求

- Python 3.7+
- tkinter (Linux 可能需額外安裝)

## 安裝 tkinter

**Ubuntu/Debian:**
```bash
sudo apt install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**Windows:** Python 已內建 tkinter

## 使用方式

### Linux / macOS
```bash
./run.sh
# 或
python3 main.py
```

### Windows
```
雙擊 run.bat
# 或
python main.py
```

## 端口

| 端口 | 協定 | 用途 |
|------|------|------|
| 52525 | UDP | 節點發現 |
| 52526 | TCP | 檔案/文字傳輸 |

請確保防火牆允許這兩個端口。

## 接收檔案位置

接收的檔案儲存在: `~/PCPCS_Received/`

## 截圖

啟動後會顯示 GUI 介面：
- 左側：已發現的電腦列表
- 右側：文字輸入框和檔案選擇器
- 底部：傳輸記錄

## License

MIT
