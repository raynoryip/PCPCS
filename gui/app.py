"""
PCPCS GUI 介面
使用 Tkinter 實作跨平台圖形介面
Modern Light Theme with Perspic Blue Accent
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import threading
import os
import sys
import json
import datetime
import time

# PIL 是可選的，用於顯示 Logo
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import get_hostname, get_local_ip, RECEIVE_DIR
from network.discovery import NetworkDiscovery, PeerInfo
from network.server import TransferServer
from network.client import TransferClient


# 本地數據目錄
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local_data")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# Perspic 淺藍色主題 (白色為主，淺藍色為輔)
COLORS = {
    "primary": "#0088FF",           # Perspic 主藍色
    "primary_light": "#E3F2FD",     # 非常淺的藍色背景
    "primary_hover": "#0066CC",     # 滑鼠懸停時的藍色
    "bg_white": "#FFFFFF",          # 白色背景
    "bg_light": "#F8FAFC",          # 淺灰白背景
    "bg_card": "#FFFFFF",           # 卡片背景
    "text_primary": "#1A1A2E",      # 主要文字 (深色)
    "text_secondary": "#64748B",    # 次要文字 (灰色)
    "border": "#E2E8F0",            # 邊框色
    "success": "#10B981",           # 成功綠
    "warning": "#F59E0B",           # 警告黃
    "error": "#EF4444",             # 錯誤紅
    "shadow": "#94A3B8",            # 陰影色
}


class RecentConnections:
    """最近連線記錄管理"""

    def __init__(self):
        self.file_path = os.path.join(DATA_DIR, "recent_connections.json")
        os.makedirs(DATA_DIR, exist_ok=True)

    def load(self) -> list:
        """載入最近連線"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save(self, connections: list):
        """儲存最近連線"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(connections, f, ensure_ascii=False, indent=2)

    def add_connection(self, ip: str, hostname: str, platform: str):
        """添加或更新連線記錄"""
        connections = self.load()
        connections = [c for c in connections if c.get("ip") != ip]
        connections.insert(0, {
            "ip": ip,
            "hostname": hostname,
            "platform": platform,
            "last_connected": datetime.datetime.now().isoformat()
        })
        connections = connections[:20]
        self.save(connections)

    def remove_connection(self, ip: str):
        """移除連線記錄"""
        connections = self.load()
        connections = [c for c in connections if c.get("ip") != ip]
        self.save(connections)


class ChatHistory:
    """聊天記錄管理"""

    def __init__(self):
        self.history_dir = os.path.join(DATA_DIR, "chat_history")
        os.makedirs(self.history_dir, exist_ok=True)

    def _get_history_file(self, peer_ip: str) -> str:
        """取得對應 IP 的歷史記錄檔案"""
        safe_ip = peer_ip.replace(".", "_")
        return os.path.join(self.history_dir, f"chat_{safe_ip}.json")

    def load_history(self, peer_ip: str) -> list:
        """載入聊天記錄"""
        filepath = self._get_history_file(peer_ip)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_message(self, peer_ip: str, sender: str, message: str, is_file: bool = False,
                     file_info: dict = None):
        """儲存訊息"""
        history = self.load_history(peer_ip)
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "sender": sender,
            "message": message,
            "is_file": is_file,
            "file_info": file_info
        }
        history.append(entry)

        filepath = self._get_history_file(peer_ip)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def clear_history(self, peer_ip: str):
        """清除聊天記錄"""
        filepath = self._get_history_file(peer_ip)
        if os.path.exists(filepath):
            os.remove(filepath)


class DiagnosticSystem:
    """診斷系統 - 檢測連接問題並提供解決方案"""

    def __init__(self):
        import platform
        self.system = platform.system()
        self.hostname = get_hostname()
        self.local_ip = get_local_ip()

    def run_full_diagnostic(self, target_ip: str = None, callback=None):
        """執行完整診斷"""
        results = {
            "system_info": self._get_system_info(),
            "network_info": self._get_network_info(),
            "port_status": self._check_ports(),
            "firewall_status": self._check_firewall(),
            "connectivity": None
        }

        if target_ip:
            results["connectivity"] = self._test_connectivity(target_ip)

        results["recommendations"] = self._generate_recommendations(results)

        if callback:
            callback(results)

        return results

    def _get_system_info(self) -> dict:
        """取得系統資訊"""
        import platform
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": self.hostname,
            "python_version": platform.python_version()
        }

    def _get_network_info(self) -> dict:
        """取得網路資訊"""
        info = {
            "local_ip": self.local_ip,
            "hostname": self.hostname,
            "discovery_port": 52525,
            "transfer_port": 52526
        }

        try:
            if self.system == "Windows":
                import subprocess
                result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=10)
                info["interfaces_raw"] = result.stdout[:1000]
            else:
                import subprocess
                result = subprocess.run(["ip", "addr"], capture_output=True, text=True, timeout=10)
                info["interfaces_raw"] = result.stdout[:1000]
        except:
            pass

        return info

    def _check_ports(self) -> dict:
        """檢查端口狀態"""
        import socket
        results = {
            "udp_52525": False,
            "tcp_52526": False,
            "udp_52525_note": "",
            "tcp_52526_note": ""
        }

        # 檢查 UDP 52525
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 52525))
            sock.close()
            results["udp_52525"] = True
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                results["udp_52525"] = True
                results["udp_52525_note"] = "PCPCS 正在監聽"

        # 檢查 TCP 52526
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 52526))
            sock.close()
            results["tcp_52526"] = True
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                results["tcp_52526"] = True
                results["tcp_52526_note"] = "PCPCS 正在監聽"

        return results

    def _check_firewall(self) -> dict:
        """檢查防火牆狀態"""
        import subprocess
        result = {
            "status": "unknown",
            "details": "",
            "pcpcs_allowed": "unknown"
        }

        try:
            if self.system == "Windows":
                proc = subprocess.run(
                    ["netsh", "advfirewall", "show", "allprofiles", "state"],
                    capture_output=True, text=True, timeout=10
                )
                result["details"] = proc.stdout
                if "ON" in proc.stdout:
                    result["status"] = "enabled"
                else:
                    result["status"] = "disabled"

            elif self.system == "Linux":
                proc = subprocess.run(
                    ["ufw", "status"],
                    capture_output=True, text=True, timeout=10
                )
                result["details"] = proc.stdout
                if "active" in proc.stdout.lower():
                    result["status"] = "enabled"
                    if "52525" in proc.stdout and "52526" in proc.stdout:
                        result["pcpcs_allowed"] = "yes"
                    else:
                        result["pcpcs_allowed"] = "no"
                else:
                    result["status"] = "disabled"

        except Exception as e:
            result["error"] = str(e)

        return result

    def _test_connectivity(self, target_ip: str) -> dict:
        """測試與目標的連接"""
        import subprocess
        import socket

        result = {
            "ping": False,
            "ping_ms": None,
            "tcp_52526": False,
            "udp_52525": "unknown"
        }

        # Ping 測試
        try:
            if self.system == "Windows":
                cmd = ["ping", "-n", "1", "-w", "2000", target_ip]
            else:
                cmd = ["ping", "-c", "1", "-W", "2", target_ip]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if proc.returncode == 0:
                result["ping"] = True
                import re
                match = re.search(r'[時间time][=<]\s*([0-9.]+)\s*ms', proc.stdout, re.IGNORECASE)
                if match:
                    result["ping_ms"] = float(match.group(1))
        except:
            pass

        # TCP 52526 測試
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((target_ip, 52526))
            sock.close()
            result["tcp_52526"] = True
        except:
            pass

        return result

    def _generate_recommendations(self, results: dict) -> list:
        """根據診斷結果生成建議"""
        recommendations = []

        fw = results.get("firewall_status", {})
        if fw.get("status") == "enabled":
            if fw.get("pcpcs_allowed") == "no":
                if self.system == "Linux":
                    recommendations.append({
                        "issue": "Linux 防火牆未開放 PCPCS 端口",
                        "solution": "執行以下命令開放端口:",
                        "commands": [
                            "sudo ufw allow 52525/udp comment 'PCPCS Discovery'",
                            "sudo ufw allow 52526/tcp comment 'PCPCS Transfer'"
                        ]
                    })
                elif self.system == "Windows":
                    recommendations.append({
                        "issue": "Windows 防火牆可能阻擋連接",
                        "solution": "在防火牆設定中允許 Python 或開放以下端口:",
                        "commands": [
                            "netsh advfirewall firewall add rule name=\"PCPCS UDP\" dir=in action=allow protocol=UDP localport=52525",
                            "netsh advfirewall firewall add rule name=\"PCPCS TCP\" dir=in action=allow protocol=TCP localport=52526"
                        ]
                    })

        conn = results.get("connectivity", {})
        if conn:
            if not conn.get("ping"):
                recommendations.append({
                    "issue": "無法 Ping 到目標電腦",
                    "solution": "確認兩台電腦在同一個網段，並檢查目標電腦的防火牆是否允許 ICMP",
                    "commands": []
                })
            elif conn.get("ping") and not conn.get("tcp_52526"):
                recommendations.append({
                    "issue": "Ping 成功但 TCP 52526 連接失敗",
                    "solution": "目標電腦的防火牆可能阻擋了 TCP 52526 端口，請在目標電腦上開放此端口",
                    "commands": []
                })

        if not recommendations:
            recommendations.append({
                "issue": "未發現問題",
                "solution": "網路設定看起來正常。如果仍無法連接，請確認目標電腦也在運行 PCPCS。",
                "commands": []
            })

        return recommendations

    def get_quick_setup_guide(self) -> str:
        """取得快速設定指南"""
        guide = f"""
╔══════════════════════════════════════════════════════════════╗
║                    PCPCS 快速設定指南                         ║
╠══════════════════════════════════════════════════════════════╣
║ 本機資訊:                                                     ║
║   電腦名稱: {self.hostname:<46} ║
║   IP 地址:  {self.local_ip:<46} ║
║   作業系統: {self.system:<46} ║
╠══════════════════════════════════════════════════════════════╣
║ 需要開放的端口:                                               ║
║   UDP 52525 - 節點發現                                        ║
║   TCP 52526 - 檔案/文字傳輸                                   ║
╠══════════════════════════════════════════════════════════════╣
"""
        if self.system == "Linux":
            guide += """║ Linux 防火牆設定:                                             ║
║   sudo ufw allow 52525/udp                                    ║
║   sudo ufw allow 52526/tcp                                    ║
╚══════════════════════════════════════════════════════════════╝
"""
        elif self.system == "Windows":
            guide += """║ Windows 防火牆設定:                                           ║
║   1. 開啟「Windows Defender 防火牆」                          ║
║   2. 點擊「允許應用程式通過防火牆」                           ║
║   3. 添加 Python 或開放 UDP 52525 和 TCP 52526                ║
╚══════════════════════════════════════════════════════════════╝
"""
        else:
            guide += """╚══════════════════════════════════════════════════════════════╝
"""
        return guide


class PCPCSApp:
    """PCPCS 主應用程式 - Modern Light Theme"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"PCPCS - {get_hostname()} ({get_local_ip()})")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        self.root.configure(bg=COLORS["bg_light"])

        # 設定樣式
        self.style = ttk.Style()
        self._setup_styles()

        # Logo
        self.logo_image = None
        self._load_logo()

        # 聊天記錄管理
        self.chat_history = ChatHistory()

        # 最近連線管理
        self.recent_connections = RecentConnections()

        # 診斷系統
        self.diagnostic = DiagnosticSystem()

        # 網路元件
        self.discovery = NetworkDiscovery(on_peer_update=self._on_peer_update)
        self.server = TransferServer(
            on_text_received=self._on_text_received,
            on_file_received=self._on_file_received,
            on_progress=self._on_receive_progress,
            on_status=self._log
        )
        self.client = TransferClient(
            on_progress=self._on_send_progress,
            on_status=self._log,
            on_complete=self._on_send_complete
        )

        # 傳輸追蹤
        self.transfer_start_time = None
        self.transfer_size = 0

        # 選中的目標
        self.selected_peer_ip = None
        self.selected_peer_name = None

        # 建立 UI
        self._create_ui()

        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_logo(self):
        """載入 Perspic Logo"""
        if not PIL_AVAILABLE:
            self.logo_image = None
            return

        try:
            logo_path = os.path.join(ASSETS_DIR, "logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                img = img.resize((120, 90), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"無法載入 Logo: {e}")
            self.logo_image = None

    def _setup_styles(self):
        """設定 Modern UI 樣式"""
        self.style.theme_use('clam')

        # 主框架
        self.style.configure('Main.TFrame', background=COLORS["bg_light"])
        self.style.configure('Card.TFrame', background=COLORS["bg_card"])

        # 標籤樣式
        self.style.configure('Title.TLabel',
                           background=COLORS["bg_light"],
                           foreground=COLORS["text_primary"],
                           font=('Segoe UI', 12, 'bold'))

        self.style.configure('Subtitle.TLabel',
                           background=COLORS["bg_light"],
                           foreground=COLORS["text_secondary"],
                           font=('Segoe UI', 9))

        self.style.configure('Card.TLabel',
                           background=COLORS["bg_card"],
                           foreground=COLORS["text_primary"],
                           font=('Segoe UI', 10))

        self.style.configure('CardTitle.TLabel',
                           background=COLORS["bg_card"],
                           foreground=COLORS["primary"],
                           font=('Segoe UI', 10, 'bold'))

        self.style.configure('Info.TLabel',
                           background=COLORS["bg_card"],
                           foreground=COLORS["text_secondary"],
                           font=('Consolas', 9))

        # LabelFrame 樣式
        self.style.configure('Card.TLabelframe',
                           background=COLORS["bg_card"],
                           foreground=COLORS["text_primary"],
                           borderwidth=1,
                           relief='solid')
        self.style.configure('Card.TLabelframe.Label',
                           background=COLORS["bg_card"],
                           foreground=COLORS["primary"],
                           font=('Segoe UI', 10, 'bold'))

        # 按鈕樣式 - 主要藍色按鈕
        self.style.configure('Primary.TButton',
                           background=COLORS["primary"],
                           foreground='white',
                           font=('Segoe UI', 9, 'bold'),
                           padding=(10, 5))
        self.style.map('Primary.TButton',
                      background=[('active', COLORS["primary_hover"]),
                                ('pressed', COLORS["primary_hover"])])

        # 次要按鈕
        self.style.configure('Secondary.TButton',
                           background=COLORS["bg_white"],
                           foreground=COLORS["text_primary"],
                           font=('Segoe UI', 9),
                           padding=(8, 4),
                           borderwidth=1)
        self.style.map('Secondary.TButton',
                      background=[('active', COLORS["primary_light"])])

        # 進度條
        self.style.configure('Blue.Horizontal.TProgressbar',
                           background=COLORS["primary"],
                           troughcolor=COLORS["border"])

        # Entry
        self.style.configure('Modern.TEntry',
                           fieldbackground=COLORS["bg_white"],
                           foreground=COLORS["text_primary"],
                           padding=5)

    def _create_ui(self):
        """建立使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10", style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側 - 節點列表和控制
        left_frame = ttk.Frame(main_frame, width=280, style='Main.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        # Logo 區域
        if self.logo_image:
            logo_label = tk.Label(left_frame, image=self.logo_image, bg=COLORS["bg_light"])
            logo_label.pack(pady=(0, 10))

        # 節點列表框
        peer_frame = ttk.LabelFrame(left_frame, text="  已發現的電腦  ", padding="8", style='Card.TLabelframe')
        peer_frame.pack(fill=tk.BOTH, expand=True)

        # 使用 Canvas + Frame 實現圓角效果的列表
        list_container = tk.Frame(peer_frame, bg=COLORS["bg_white"], highlightthickness=1,
                                 highlightbackground=COLORS["border"])
        list_container.pack(fill=tk.BOTH, expand=True)

        self.peer_listbox = tk.Listbox(
            list_container,
            font=('Consolas', 9),
            selectbackground=COLORS["primary"],
            selectforeground='white',
            bg=COLORS["bg_white"],
            fg=COLORS["text_primary"],
            borderwidth=0,
            highlightthickness=0,
            activestyle='none'
        )
        self.peer_listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.peer_listbox.bind('<<ListboxSelect>>', self._on_peer_select)

        # 按鈕框
        btn_frame = ttk.Frame(peer_frame, style='Card.TFrame')
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(btn_frame, text="重新掃描", command=self._refresh_peers,
                  style='Secondary.TButton').pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="手動添加 IP", command=self._manual_add_ip,
                  style='Secondary.TButton').pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="測試連接", command=self._manual_ping,
                  style='Secondary.TButton').pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="網路診斷", command=self._show_diagnostic,
                  style='Secondary.TButton').pack(fill=tk.X, pady=2)

        # 最近連線
        recent_frame = ttk.LabelFrame(left_frame, text="  最近連線  ", padding="8", style='Card.TLabelframe')
        recent_frame.pack(fill=tk.X, pady=(10, 0))

        recent_container = tk.Frame(recent_frame, bg=COLORS["bg_white"], highlightthickness=1,
                                   highlightbackground=COLORS["border"])
        recent_container.pack(fill=tk.X)

        self.recent_listbox = tk.Listbox(
            recent_container,
            font=('Consolas', 8),
            height=4,
            selectbackground=COLORS["primary"],
            selectforeground='white',
            bg=COLORS["bg_white"],
            fg=COLORS["text_secondary"],
            borderwidth=0,
            highlightthickness=0
        )
        self.recent_listbox.pack(fill=tk.X, padx=2, pady=2)
        self.recent_listbox.bind('<Double-Button-1>', self._on_recent_double_click)

        self._update_recent_list()

        # 本機資訊
        info_frame = ttk.LabelFrame(left_frame, text="  本機資訊  ", padding="8", style='Card.TLabelframe')
        info_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(info_frame, text=f"名稱: {get_hostname()}", style='Info.TLabel').pack(anchor='w')
        ttk.Label(info_frame, text=f"IP: {get_local_ip()}", style='Info.TLabel').pack(anchor='w')
        ttk.Label(info_frame, text=f"發現: UDP 52525", style='Info.TLabel').pack(anchor='w')
        ttk.Label(info_frame, text=f"傳輸: TCP 52526", style='Info.TLabel').pack(anchor='w')

        # 右側 - 聊天和傳輸區
        right_frame = ttk.Frame(main_frame, style='Main.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 目標顯示
        target_frame = ttk.Frame(right_frame, style='Main.TFrame')
        target_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(target_frame, text="對話對象:", style='Title.TLabel').pack(side=tk.LEFT)
        self.target_label = ttk.Label(target_frame, text="(請從左側選擇電腦)",
                                     style='Subtitle.TLabel')
        self.target_label.pack(side=tk.LEFT, padx=(10, 0))

        # 聊天對話框
        chat_frame = ttk.LabelFrame(right_frame, text="  對話  ", padding="8", style='Card.TLabelframe')
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 聊天記錄顯示區
        chat_container = tk.Frame(chat_frame, bg=COLORS["bg_white"], highlightthickness=1,
                                 highlightbackground=COLORS["border"])
        chat_container.pack(fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_container, height=15, font=('Consolas', 10),
            state='disabled', wrap=tk.WORD,
            bg=COLORS["bg_white"], fg=COLORS["text_primary"],
            borderwidth=0, highlightthickness=0
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 設定聊天顯示的標籤樣式
        self.chat_display.tag_configure('self', foreground=COLORS["success"], font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('peer', foreground=COLORS["primary"], font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('system', foreground=COLORS["text_secondary"], font=('Consolas', 9, 'italic'))
        self.chat_display.tag_configure('file', foreground='#7C3AED', font=('Consolas', 10))
        self.chat_display.tag_configure('timestamp', foreground=COLORS["text_secondary"], font=('Consolas', 8))

        # 輸入區
        input_frame = ttk.Frame(chat_frame, style='Card.TFrame')
        input_frame.pack(fill=tk.X, pady=(8, 0))

        input_container = tk.Frame(input_frame, bg=COLORS["bg_white"], highlightthickness=1,
                                  highlightbackground=COLORS["border"])
        input_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.message_input = tk.Entry(
            input_container, font=('Segoe UI', 11),
            bg=COLORS["bg_white"], fg=COLORS["text_primary"],
            borderwidth=0, highlightthickness=0
        )
        self.message_input.pack(fill=tk.X, padx=8, pady=6)
        self.message_input.bind('<Return>', lambda e: self._send_text())

        self.send_btn = ttk.Button(input_frame, text="發送", command=self._send_text,
                                  width=8, style='Primary.TButton')
        self.send_btn.pack(side=tk.LEFT)

        # 聊天控制按鈕
        chat_btn_frame = ttk.Frame(chat_frame, style='Card.TFrame')
        chat_btn_frame.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(chat_btn_frame, text="清除記錄", command=self._clear_chat_history,
                  style='Secondary.TButton').pack(side=tk.LEFT)
        ttk.Button(chat_btn_frame, text="開啟記錄資料夾", command=self._open_data_folder,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=8)

        # 檔案傳輸區
        file_frame = ttk.LabelFrame(right_frame, text="  檔案傳輸  ", padding="8", style='Card.TLabelframe')
        file_frame.pack(fill=tk.X, pady=(0, 10))

        file_select_frame = ttk.Frame(file_frame, style='Card.TFrame')
        file_select_frame.pack(fill=tk.X)

        file_entry_container = tk.Frame(file_select_frame, bg=COLORS["bg_white"], highlightthickness=1,
                                       highlightbackground=COLORS["border"])
        file_entry_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(
            file_entry_container, textvariable=self.file_path_var,
            font=('Consolas', 10),
            bg=COLORS["bg_white"], fg=COLORS["text_primary"],
            borderwidth=0, highlightthickness=0
        )
        self.file_entry.pack(fill=tk.X, padx=6, pady=4)

        ttk.Button(file_select_frame, text="選擇", command=self._browse_file,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 8))
        self.send_file_btn = ttk.Button(file_select_frame, text="發送檔案", command=self._send_file,
                                       style='Primary.TButton')
        self.send_file_btn.pack(side=tk.LEFT)

        # 進度條
        progress_frame = ttk.Frame(file_frame, style='Card.TFrame')
        progress_frame.pack(fill=tk.X, pady=(8, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100,
                                           style='Blue.Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(progress_frame, text="", style='Info.TLabel')
        self.progress_label.pack(anchor='w', pady=(4, 0))

        # 系統日誌
        log_frame = ttk.LabelFrame(right_frame, text="  系統日誌  ", padding="8", style='Card.TLabelframe')
        log_frame.pack(fill=tk.X)

        log_container = tk.Frame(log_frame, bg=COLORS["bg_white"], highlightthickness=1,
                                highlightbackground=COLORS["border"])
        log_container.pack(fill=tk.X)

        self.log_text = scrolledtext.ScrolledText(
            log_container, height=4, font=('Consolas', 8),
            state='disabled', wrap=tk.WORD,
            bg=COLORS["bg_white"], fg=COLORS["text_secondary"],
            borderwidth=0, highlightthickness=0
        )
        self.log_text.pack(fill=tk.X, padx=2, pady=2)

    def _update_recent_list(self):
        """更新最近連線列表"""
        self.recent_listbox.delete(0, tk.END)
        for conn in self.recent_connections.load()[:5]:
            hostname = conn.get("hostname", "Unknown")
            ip = conn.get("ip", "")
            self.recent_listbox.insert(tk.END, f"{hostname} ({ip})")

    def _on_recent_double_click(self, event):
        """雙擊最近連線"""
        selection = self.recent_listbox.curselection()
        if selection:
            connections = self.recent_connections.load()
            if selection[0] < len(connections):
                conn = connections[selection[0]]
                ip = conn.get("ip")
                hostname = conn.get("hostname")
                platform_name = conn.get("platform", "Unknown")

                # 添加到 peers
                if ip not in self.discovery.peers:
                    peer = PeerInfo(ip, hostname, platform_name)
                    self.discovery.peers[ip] = peer
                    self._update_peer_list(self.discovery.peers)

                # 選擇這個 peer
                self.selected_peer_ip = ip
                self.selected_peer_name = hostname
                self.target_label.config(text=f"{hostname} ({ip})")
                self._load_chat_history()

                # 更新選擇狀態
                for i in range(self.peer_listbox.size()):
                    if ip in self.peer_listbox.get(i):
                        self.peer_listbox.selection_clear(0, tk.END)
                        self.peer_listbox.selection_set(i)
                        break

                self._log(f"已選擇最近連線: {hostname}")

    def _on_peer_update(self, peers: dict):
        """節點列表更新回調"""
        self.root.after(0, lambda: self._update_peer_list(peers))

    def _update_peer_list(self, peers: dict):
        """更新節點列表"""
        current_selection = self.selected_peer_ip

        self.peer_listbox.delete(0, tk.END)

        for ip, peer in peers.items():
            status = "●" if peer.is_reachable else "○"
            ping_str = f"{peer.ping_ms:.0f}ms" if peer.ping_ms else "---"
            os_icon = "🐧" if "Linux" in peer.platform else "🪟" if "Windows" in peer.platform else "🍎" if "Darwin" in peer.platform else "💻"
            display = f"{status} {os_icon} {peer.hostname} ({ip}) [{ping_str}]"
            self.peer_listbox.insert(tk.END, display)

        if current_selection:
            for i in range(self.peer_listbox.size()):
                if current_selection in self.peer_listbox.get(i):
                    self.peer_listbox.selection_set(i)
                    break

    def _on_peer_select(self, event):
        """選擇節點"""
        selection = self.peer_listbox.curselection()
        if selection:
            item = self.peer_listbox.get(selection[0])
            import re
            match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', item)
            if match:
                self.selected_peer_ip = match.group(1)
                hostname_match = re.search(r'[●○]\s+.\s+(.+?)\s+\(', item)
                self.selected_peer_name = hostname_match.group(1) if hostname_match else self.selected_peer_ip
                self.target_label.config(text=f"{self.selected_peer_name} ({self.selected_peer_ip})")
                self._log(f"已選擇: {self.selected_peer_name}")
                self._load_chat_history()

                # 更新最近連線
                if self.selected_peer_ip in self.discovery.peers:
                    peer = self.discovery.peers[self.selected_peer_ip]
                    self.recent_connections.add_connection(
                        self.selected_peer_ip,
                        self.selected_peer_name,
                        peer.platform
                    )
                    self._update_recent_list()

    def _ensure_peer_exists(self, sender_ip: str, sender_name: str, sender_platform: str):
        """確保發送者存在於 peer 列表中"""
        if sender_ip not in self.discovery.peers:
            peer = PeerInfo(sender_ip, sender_name, sender_platform)
            peer.is_reachable = True
            self.discovery.peers[sender_ip] = peer
            self.root.after(0, lambda: self._update_peer_list(self.discovery.peers))
            self._log(f"自動添加節點: {sender_name} ({sender_ip})")

    def _load_chat_history(self):
        """載入並顯示聊天記錄"""
        if not self.selected_peer_ip:
            return

        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)

        history = self.chat_history.load_history(self.selected_peer_ip)

        for entry in history:
            timestamp = datetime.datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            sender = entry["sender"]
            message = entry["message"]
            is_file = entry.get("is_file", False)

            self.chat_display.insert(tk.END, f"[{timestamp}]\n", 'timestamp')

            if sender == get_hostname():
                self.chat_display.insert(tk.END, f"  {sender} (我): ", 'self')
            else:
                self.chat_display.insert(tk.END, f"  {sender}: ", 'peer')

            if is_file:
                file_info = entry.get("file_info", {})
                size_str = self._format_size(file_info.get("size", 0))
                speed_str = file_info.get("speed", "")
                self.chat_display.insert(tk.END, f"[檔案] {message} ({size_str}) {speed_str}\n", 'file')
            else:
                self.chat_display.insert(tk.END, f"{message}\n", '')

            self.chat_display.insert(tk.END, "\n", '')

        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def _add_chat_message(self, sender: str, message: str, is_file: bool = False, file_info: dict = None):
        """添加聊天訊息到顯示區"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"[{timestamp}]\n", 'timestamp')

        if sender == get_hostname():
            self.chat_display.insert(tk.END, f"  {sender} (我): ", 'self')
        else:
            self.chat_display.insert(tk.END, f"  {sender}: ", 'peer')

        if is_file:
            size_str = self._format_size(file_info.get("size", 0)) if file_info else ""
            speed_str = file_info.get("speed", "") if file_info else ""
            self.chat_display.insert(tk.END, f"[檔案] {message} ({size_str}) {speed_str}\n", 'file')
        else:
            self.chat_display.insert(tk.END, f"{message}\n", '')

        self.chat_display.insert(tk.END, "\n", '')
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

        if self.selected_peer_ip:
            self.chat_history.save_message(
                self.selected_peer_ip, sender, message,
                is_file=is_file, file_info=file_info
            )

    def _clear_chat_history(self):
        """清除聊天記錄"""
        if not self.selected_peer_ip:
            messagebox.showwarning("提示", "請先選擇一個對話對象")
            return

        result = messagebox.askyesno(
            "確認清除",
            f"確定要清除與 {self.selected_peer_name} 的所有聊天記錄嗎?\n此操作無法復原。\n\n注意: 電腦仍會保留在列表中。"
        )

        if result:
            self.chat_history.clear_history(self.selected_peer_ip)
            self.chat_display.config(state='normal')
            self.chat_display.delete('1.0', tk.END)
            self.chat_display.config(state='disabled')
            self._log("聊天記錄已清除")

    def _open_data_folder(self):
        """開啟本地數據資料夾"""
        os.makedirs(DATA_DIR, exist_ok=True)
        import platform
        import subprocess

        if platform.system() == "Windows":
            os.startfile(DATA_DIR)
        elif platform.system() == "Darwin":
            subprocess.run(["open", DATA_DIR])
        else:
            subprocess.run(["xdg-open", DATA_DIR])

    def _refresh_peers(self):
        """重新掃描節點"""
        self._log("正在重新掃描網路...")
        self.discovery.peers.clear()
        self._update_peer_list({})

    def _manual_ping(self):
        """手動 Ping 選中的節點"""
        if not self.selected_peer_ip:
            messagebox.showwarning("提示", "請先選擇一個目標電腦")
            return

        self._log(f"正在 Ping {self.selected_peer_ip}...")

        def do_ping():
            result = self.discovery.manual_ping(self.selected_peer_ip)
            if result:
                self._log(f"Ping {self.selected_peer_ip}: {result:.1f}ms - 連接正常")
            else:
                self._log(f"Ping {self.selected_peer_ip}: 無回應")

        threading.Thread(target=do_ping, daemon=True).start()

    def _manual_add_ip(self):
        """手動添加 IP 地址"""
        ip = simpledialog.askstring("手動添加 IP", "請輸入目標電腦的 IP 地址:", parent=self.root)

        if ip and ip.strip():
            ip = ip.strip()
            self._log(f"正在嘗試連接 {ip}...")

            def try_connect():
                ping_result = self.discovery.manual_ping(ip)
                hostname = f"Manual-{ip}"
                platform_name = "Unknown"

                peer = PeerInfo(ip, hostname, platform_name)
                peer.ping_ms = ping_result
                peer.is_reachable = ping_result is not None
                self.discovery.peers[ip] = peer

                if ping_result:
                    self._log(f"成功添加 {ip} (Ping: {ping_result:.1f}ms)")
                else:
                    self._log(f"已添加 {ip} (無法 Ping)")

                # 自動選擇這個 peer
                def select_peer():
                    self._update_peer_list(self.discovery.peers)
                    self.selected_peer_ip = ip
                    self.selected_peer_name = hostname
                    self.target_label.config(text=f"{hostname} ({ip})")
                    self._load_chat_history()

                    # 更新選擇狀態
                    for i in range(self.peer_listbox.size()):
                        if ip in self.peer_listbox.get(i):
                            self.peer_listbox.selection_clear(0, tk.END)
                            self.peer_listbox.selection_set(i)
                            break

                self.root.after(0, select_peer)

            threading.Thread(target=try_connect, daemon=True).start()

    def _show_diagnostic(self):
        """顯示診斷視窗"""
        diag_window = tk.Toplevel(self.root)
        diag_window.title("網路診斷")
        diag_window.geometry("700x550")
        diag_window.transient(self.root)
        diag_window.configure(bg=COLORS["bg_light"])

        # 診斷結果顯示
        result_container = tk.Frame(diag_window, bg=COLORS["bg_white"], highlightthickness=1,
                                   highlightbackground=COLORS["border"])
        result_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        result_text = scrolledtext.ScrolledText(
            result_container, font=('Consolas', 10),
            bg=COLORS["bg_white"], fg=COLORS["text_primary"],
            borderwidth=0, highlightthickness=0
        )
        result_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        guide = self.diagnostic.get_quick_setup_guide()
        result_text.insert(tk.END, guide)
        result_text.insert(tk.END, "\n\n正在執行診斷...\n")

        btn_frame = ttk.Frame(diag_window, style='Main.TFrame')
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def run_diagnostic():
            result_text.delete('1.0', tk.END)
            result_text.insert(tk.END, guide)
            result_text.insert(tk.END, "\n\n正在執行診斷...\n")
            result_text.update()

            target = self.selected_peer_ip

            def on_complete(results):
                diag_window.after(0, lambda: show_results(results))

            def show_results(results):
                result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
                result_text.insert(tk.END, "診斷結果:\n")
                result_text.insert(tk.END, "=" * 60 + "\n\n")

                sys_info = results.get("system_info", {})
                result_text.insert(tk.END, f"作業系統: {sys_info.get('os', 'Unknown')} {sys_info.get('os_version', '')[:30]}\n")

                ports = results.get("port_status", {})
                result_text.insert(tk.END, f"\n端口狀態:\n")
                udp_status = '✓ 可用' if ports.get('udp_52525') else '✗ 不可用'
                tcp_status = '✓ 可用' if ports.get('tcp_52526') else '✗ 不可用'
                udp_note = f" ({ports.get('udp_52525_note', '')})" if ports.get('udp_52525_note') else ""
                tcp_note = f" ({ports.get('tcp_52526_note', '')})" if ports.get('tcp_52526_note') else ""
                result_text.insert(tk.END, f"  UDP 52525: {udp_status}{udp_note}\n")
                result_text.insert(tk.END, f"  TCP 52526: {tcp_status}{tcp_note}\n")

                fw = results.get("firewall_status", {})
                result_text.insert(tk.END, f"\n防火牆: {fw.get('status', 'unknown')}\n")

                conn = results.get("connectivity")
                if conn:
                    result_text.insert(tk.END, f"\n連接測試 ({target}):\n")
                    result_text.insert(tk.END, f"  Ping: {'✓ 成功' if conn.get('ping') else '✗ 失敗'}")
                    if conn.get('ping_ms'):
                        result_text.insert(tk.END, f" ({conn['ping_ms']:.1f}ms)")
                    result_text.insert(tk.END, f"\n  TCP 52526: {'✓ 連通' if conn.get('tcp_52526') else '✗ 不通'}\n")

                result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
                result_text.insert(tk.END, "建議:\n")
                result_text.insert(tk.END, "=" * 60 + "\n\n")

                for rec in results.get("recommendations", []):
                    result_text.insert(tk.END, f"● {rec['issue']}\n")
                    result_text.insert(tk.END, f"  {rec['solution']}\n")
                    for cmd in rec.get("commands", []):
                        result_text.insert(tk.END, f"    $ {cmd}\n")
                    result_text.insert(tk.END, "\n")

                result_text.see(tk.END)

            threading.Thread(
                target=lambda: self.diagnostic.run_full_diagnostic(target, on_complete),
                daemon=True
            ).start()

        ttk.Button(btn_frame, text="重新診斷", command=run_diagnostic,
                  style='Secondary.TButton').pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="複製資訊",
                  command=lambda: self._copy_to_clipboard(result_text.get('1.0', tk.END)),
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="關閉", command=diag_window.destroy,
                  style='Primary.TButton').pack(side=tk.RIGHT)

        diag_window.after(100, run_diagnostic)

    def _copy_to_clipboard(self, text):
        """複製到剪貼簿"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("提示", "已複製到剪貼簿")

    def _browse_file(self):
        """選擇檔案"""
        filepath = filedialog.askopenfilename(title="選擇要發送的檔案")
        if filepath:
            self.file_path_var.set(filepath)

    def _send_text(self):
        """發送文字"""
        if not self.selected_peer_ip:
            messagebox.showwarning("提示", "請先選擇一個目標電腦")
            return

        text = self.message_input.get().strip()
        if not text:
            return

        self.message_input.delete(0, tk.END)
        self._add_chat_message(get_hostname(), text)
        self._log(f"正在發送文字...")
        self.send_btn.config(state='disabled')
        self.client.send_text(self.selected_peer_ip, text)

    def _send_file(self):
        """發送檔案"""
        if not self.selected_peer_ip:
            messagebox.showwarning("提示", "請先選擇一個目標電腦")
            return

        filepath = self.file_path_var.get()
        if not filepath or not os.path.exists(filepath):
            messagebox.showwarning("提示", "請選擇有效的檔案")
            return

        self.transfer_size = os.path.getsize(filepath)
        self.transfer_start_time = time.time()

        self._log(f"正在發送檔案...")
        self.send_file_btn.config(state='disabled')
        self.progress_var.set(0)
        self.client.send_file(self.selected_peer_ip, filepath)

    def _on_send_progress(self, progress: float, message: str):
        """發送進度回調"""
        self.root.after(0, lambda: self._update_progress(progress, message))

    def _on_receive_progress(self, progress: float, message: str):
        """接收進度回調"""
        self.root.after(0, lambda: self._update_progress(progress, message))

    def _update_progress(self, progress: float, message: str):
        """更新進度條"""
        self.progress_var.set(progress)

        speed_str = ""
        if self.transfer_start_time and self.transfer_size > 0:
            elapsed = time.time() - self.transfer_start_time
            if elapsed > 0:
                speed = (progress / 100 * self.transfer_size) / elapsed
                speed_str = f" | {self._format_size(speed)}/s"

        self.progress_label.config(text=f"{message} ({progress:.1f}%){speed_str}")

    def _on_send_complete(self, success: bool, message: str):
        """發送完成回調"""
        self.root.after(0, lambda: self._handle_send_complete(success, message))

    def _handle_send_complete(self, success: bool, message: str):
        """處理發送完成"""
        self.send_btn.config(state='normal')
        self.send_file_btn.config(state='normal')
        self.progress_var.set(100 if success else 0)

        speed_str = ""
        if self.transfer_start_time and self.transfer_size > 0 and success:
            elapsed = time.time() - self.transfer_start_time
            if elapsed > 0:
                speed = self.transfer_size / elapsed
                speed_str = f"{self._format_size(speed)}/s"

        self.progress_label.config(text=message)

        if success:
            self._log(f"發送成功 {speed_str}")
            if "檔案" in message or "file" in message.lower():
                filename = self.file_path_var.get()
                if filename:
                    self._add_chat_message(
                        get_hostname(),
                        os.path.basename(filename),
                        is_file=True,
                        file_info={"size": self.transfer_size, "speed": speed_str}
                    )
        else:
            self._log(f"發送失敗: {message}")

        self.transfer_start_time = None
        self.transfer_size = 0

    def _on_text_received(self, sender_ip: str, sender_name: str, text: str, sender_platform: str = "Unknown"):
        """收到文字回調"""
        self.root.after(0, lambda: self._handle_text_received(sender_ip, sender_name, text, sender_platform))

    def _handle_text_received(self, sender_ip: str, sender_name: str, text: str, sender_platform: str = "Unknown"):
        """處理收到的文字"""
        # 確保發送者在 peer 列表中
        self._ensure_peer_exists(sender_ip, sender_name, sender_platform)

        if self.selected_peer_ip == sender_ip:
            self._add_chat_message(sender_name, text)
        else:
            self.chat_history.save_message(sender_ip, sender_name, text)
            self.chat_display.config(state='normal')
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
            self.chat_display.insert(tk.END, f"收到來自 {sender_name} ({sender_ip}) 的新訊息\n", 'system')
            self.chat_display.see(tk.END)
            self.chat_display.config(state='disabled')

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._log(f"收到文字 (已複製到剪貼簿)")

    def _on_file_received(self, sender_ip: str, sender_name: str, filepath: str, filesize: int, sender_platform: str = "Unknown"):
        """收到檔案回調"""
        self.root.after(0, lambda: self._handle_file_received(sender_ip, sender_name, filepath, filesize, sender_platform))

    def _handle_file_received(self, sender_ip: str, sender_name: str, filepath: str, filesize: int, sender_platform: str = "Unknown"):
        """處理收到的檔案"""
        # 確保發送者在 peer 列表中
        self._ensure_peer_exists(sender_ip, sender_name, sender_platform)

        filename = os.path.basename(filepath)
        size_str = self._format_size(filesize)

        file_info = {"size": filesize, "path": filepath}

        if self.selected_peer_ip == sender_ip:
            self._add_chat_message(sender_name, filename, is_file=True, file_info=file_info)
        else:
            self.chat_history.save_message(sender_ip, sender_name, filename, is_file=True, file_info=file_info)

        self._log(f"收到檔案: {filename} ({size_str})")

        result = messagebox.askyesno(
            f"收到檔案 - {sender_name}",
            f"檔案: {filename}\n大小: {size_str}\n\n是否開啟檔案所在資料夾?"
        )
        if result:
            self._open_receive_folder()

    def _open_receive_folder(self):
        """開啟接收資料夾"""
        os.makedirs(RECEIVE_DIR, exist_ok=True)
        import platform
        import subprocess

        if platform.system() == "Windows":
            os.startfile(RECEIVE_DIR)
        elif platform.system() == "Darwin":
            subprocess.run(["open", RECEIVE_DIR])
        else:
            subprocess.run(["xdg-open", RECEIVE_DIR])

    def _format_size(self, size: int) -> str:
        """格式化檔案大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _log(self, message: str):
        """寫入系統日誌"""
        def _write():
            self.log_text.config(state='normal')
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')

        self.root.after(0, _write)

    def _on_close(self):
        """關閉視窗"""
        self.discovery.stop()
        self.server.stop()
        self.root.destroy()

    def run(self):
        """執行應用程式"""
        self._log("正在啟動 PCPCS...")
        self.discovery.start()
        self.server.start()
        self._log(f"服務已啟動，正在掃描區域網路...")
        self._log(f"接收檔案位置: {RECEIVE_DIR}")

        self.root.mainloop()


def main():
    if not PIL_AVAILABLE:
        print("提示: 安裝 Pillow 可顯示 Logo (pip install Pillow)")

    app = PCPCSApp()
    app.run()


if __name__ == "__main__":
    main()
