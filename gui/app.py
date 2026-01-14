"""
PCPCS GUI 介面
使用 Tkinter 實作跨平台圖形介面
Modern Light Theme with Perspic Blue Accent
Supports Traditional Chinese and English
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import threading
import os
import sys
import json
import datetime
import time

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
    "primary": "#0088FF",
    "primary_light": "#E3F2FD",
    "primary_hover": "#0066CC",
    "bg_white": "#FFFFFF",
    "bg_light": "#F8FAFC",
    "bg_card": "#FFFFFF",
    "text_primary": "#1A1A2E",
    "text_secondary": "#64748B",
    "border": "#E2E8F0",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "shadow": "#94A3B8",
}

# 語言字典
LANG = {
    "zh-TW": {
        "window_title": "PCPCS",
        "discovered_computers": "已發現的電腦",
        "rescan": "重新掃描",
        "manual_add_ip": "手動添加 IP",
        "test_connection": "測試連接",
        "network_diagnostic": "網路診斷",
        "recent_connections": "最近連線",
        "local_info": "本機資訊",
        "name": "名稱",
        "ip": "IP",
        "discovery_port": "發現",
        "transfer_port": "傳輸",
        "chat_target": "對話對象:",
        "select_computer": "(請從左側選擇電腦)",
        "conversation": "對話",
        "clear_history": "清除記錄",
        "open_data_folder": "開啟記錄資料夾",
        "file_transfer": "檔案傳輸",
        "select": "選擇",
        "send_file": "發送檔案",
        "system_log": "系統日誌",
        "send": "發送",
        "me": "我",
        "file_label": "[檔案]",
        "confirm_clear": "確認清除",
        "confirm_clear_msg": "確定要清除與 {name} 的所有聊天記錄嗎?\n此操作無法復原。\n\n注意: 電腦仍會保留在列表中。",
        "hint": "提示",
        "select_target_first": "請先選擇一個目標電腦",
        "select_valid_file": "請選擇有效的檔案",
        "select_chat_target": "請先選擇一個對話對象",
        "scanning": "正在重新掃描網路...",
        "pinging": "正在 Ping {ip}...",
        "ping_success": "Ping {ip}: {ms:.1f}ms - 連接正常",
        "ping_fail": "Ping {ip}: 無回應",
        "trying_connect": "正在嘗試連接 {ip}...",
        "add_success": "成功添加 {ip} (Ping: {ms:.1f}ms)",
        "add_no_ping": "已添加 {ip} (無法 Ping)",
        "selected": "已選擇: {name}",
        "selected_recent": "已選擇最近連線: {name}",
        "auto_add_peer": "自動添加節點: {name} ({ip})",
        "history_cleared": "聊天記錄已清除",
        "sending_text": "正在發送文字...",
        "sending_file": "正在發送檔案...",
        "send_success": "發送成功",
        "send_fail": "發送失敗: {msg}",
        "received_text": "收到文字 (已複製到剪貼簿)",
        "received_file": "收到檔案: {name} ({size})",
        "new_message_from": "收到來自 {name} ({ip}) 的新訊息",
        "file_received_title": "收到檔案 - {name}",
        "file_received_msg": "檔案: {filename}\n大小: {size}\n\n是否開啟檔案所在資料夾?",
        "starting": "正在啟動 PCPCS...",
        "service_started": "服務已啟動，正在掃描區域網路...",
        "receive_location": "接收檔案位置: {path}",
        "diagnostic_title": "網路診斷",
        "diagnostic_running": "正在執行診斷...",
        "diagnostic_result": "診斷結果:",
        "os_label": "作業系統",
        "port_status": "端口狀態",
        "available": "可用",
        "unavailable": "不可用",
        "pcpcs_listening": "PCPCS 正在監聽",
        "firewall": "防火牆",
        "connection_test": "連接測試",
        "ping_label": "Ping",
        "success": "成功",
        "fail": "失敗",
        "connected": "連通",
        "not_connected": "不通",
        "recommendations": "建議",
        "re_diagnose": "重新診斷",
        "copy_info": "複製資訊",
        "close": "關閉",
        "copied": "已複製到剪貼簿",
        "manual_add_title": "手動添加 IP",
        "enter_ip": "請輸入目標電腦的 IP 地址:",
        "select_file_title": "選擇要發送的檔案",
        "language": "Language",
        "switch_to_en": "English",
        "switch_to_zh": "繁體中文",
        "quick_setup_guide": "PCPCS 快速設定指南",
        "local_info_label": "本機資訊:",
        "computer_name": "電腦名稱",
        "ip_address": "IP 地址",
        "operating_system": "作業系統",
        "ports_to_open": "需要開放的端口:",
        "node_discovery": "節點發現",
        "file_text_transfer": "檔案/文字傳輸",
        "linux_firewall": "Linux 防火牆設定:",
        "windows_firewall": "Windows 防火牆設定:",
        "win_fw_step1": "1. 開啟「Windows Defender 防火牆」",
        "win_fw_step2": "2. 點擊「允許應用程式通過防火牆」",
        "win_fw_step3": "3. 添加 Python 或開放 UDP 52525 和 TCP 52526",
        "issue_linux_fw": "Linux 防火牆未開放 PCPCS 端口",
        "solution_linux_fw": "執行以下命令開放端口:",
        "issue_win_fw": "Windows 防火牆可能阻擋連接",
        "solution_win_fw": "在防火牆設定中允許 Python 或開放以下端口:",
        "issue_no_ping": "無法 Ping 到目標電腦",
        "solution_no_ping": "確認兩台電腦在同一個網段，並檢查目標電腦的防火牆是否允許 ICMP",
        "issue_tcp_fail": "Ping 成功但 TCP 52526 連接失敗",
        "solution_tcp_fail": "目標電腦的防火牆可能阻擋了 TCP 52526 端口，請在目標電腦上開放此端口",
        "issue_none": "未發現問題",
        "solution_none": "網路設定看起來正常。如果仍無法連接，請確認目標電腦也在運行 PCPCS。",
    },
    "en": {
        "window_title": "PCPCS",
        "discovered_computers": "Discovered Computers",
        "rescan": "Rescan",
        "manual_add_ip": "Add IP Manually",
        "test_connection": "Test Connection",
        "network_diagnostic": "Network Diagnostic",
        "recent_connections": "Recent Connections",
        "local_info": "Local Info",
        "name": "Name",
        "ip": "IP",
        "discovery_port": "Discovery",
        "transfer_port": "Transfer",
        "chat_target": "Chat Target:",
        "select_computer": "(Select a computer from the left)",
        "conversation": "Conversation",
        "clear_history": "Clear History",
        "open_data_folder": "Open Data Folder",
        "file_transfer": "File Transfer",
        "select": "Browse",
        "send_file": "Send File",
        "system_log": "System Log",
        "send": "Send",
        "me": "Me",
        "file_label": "[File]",
        "confirm_clear": "Confirm Clear",
        "confirm_clear_msg": "Are you sure you want to clear all chat history with {name}?\nThis action cannot be undone.\n\nNote: The computer will remain in the list.",
        "hint": "Notice",
        "select_target_first": "Please select a target computer first",
        "select_valid_file": "Please select a valid file",
        "select_chat_target": "Please select a chat target first",
        "scanning": "Rescanning network...",
        "pinging": "Pinging {ip}...",
        "ping_success": "Ping {ip}: {ms:.1f}ms - Connection OK",
        "ping_fail": "Ping {ip}: No response",
        "trying_connect": "Trying to connect to {ip}...",
        "add_success": "Successfully added {ip} (Ping: {ms:.1f}ms)",
        "add_no_ping": "Added {ip} (Unable to ping)",
        "selected": "Selected: {name}",
        "selected_recent": "Selected recent connection: {name}",
        "auto_add_peer": "Auto-added peer: {name} ({ip})",
        "history_cleared": "Chat history cleared",
        "sending_text": "Sending text...",
        "sending_file": "Sending file...",
        "send_success": "Send successful",
        "send_fail": "Send failed: {msg}",
        "received_text": "Text received (copied to clipboard)",
        "received_file": "File received: {name} ({size})",
        "new_message_from": "New message from {name} ({ip})",
        "file_received_title": "File Received - {name}",
        "file_received_msg": "File: {filename}\nSize: {size}\n\nOpen the containing folder?",
        "starting": "Starting PCPCS...",
        "service_started": "Service started, scanning local network...",
        "receive_location": "Receive location: {path}",
        "diagnostic_title": "Network Diagnostic",
        "diagnostic_running": "Running diagnostic...",
        "diagnostic_result": "Diagnostic Result:",
        "os_label": "Operating System",
        "port_status": "Port Status",
        "available": "Available",
        "unavailable": "Unavailable",
        "pcpcs_listening": "PCPCS is listening",
        "firewall": "Firewall",
        "connection_test": "Connection Test",
        "ping_label": "Ping",
        "success": "Success",
        "fail": "Failed",
        "connected": "Connected",
        "not_connected": "Not connected",
        "recommendations": "Recommendations",
        "re_diagnose": "Re-diagnose",
        "copy_info": "Copy Info",
        "close": "Close",
        "copied": "Copied to clipboard",
        "manual_add_title": "Add IP Manually",
        "enter_ip": "Enter the target computer's IP address:",
        "select_file_title": "Select file to send",
        "language": "語言",
        "switch_to_en": "English",
        "switch_to_zh": "繁體中文",
        "quick_setup_guide": "PCPCS Quick Setup Guide",
        "local_info_label": "Local Info:",
        "computer_name": "Computer Name",
        "ip_address": "IP Address",
        "operating_system": "Operating System",
        "ports_to_open": "Ports to open:",
        "node_discovery": "Node Discovery",
        "file_text_transfer": "File/Text Transfer",
        "linux_firewall": "Linux Firewall Setup:",
        "windows_firewall": "Windows Firewall Setup:",
        "win_fw_step1": "1. Open 'Windows Defender Firewall'",
        "win_fw_step2": "2. Click 'Allow an app through firewall'",
        "win_fw_step3": "3. Add Python or open UDP 52525 and TCP 52526",
        "issue_linux_fw": "Linux firewall is blocking PCPCS ports",
        "solution_linux_fw": "Run these commands to open ports:",
        "issue_win_fw": "Windows firewall may be blocking connection",
        "solution_win_fw": "Allow Python in firewall settings or open these ports:",
        "issue_no_ping": "Cannot ping target computer",
        "solution_no_ping": "Make sure both computers are on the same network and check if the target's firewall allows ICMP",
        "issue_tcp_fail": "Ping succeeded but TCP 52526 connection failed",
        "solution_tcp_fail": "The target's firewall may be blocking TCP 52526. Please open this port on the target computer",
        "issue_none": "No issues found",
        "solution_none": "Network settings look fine. If you still can't connect, make sure PCPCS is running on the target computer.",
    }
}


class RecentConnections:
    """最近連線記錄管理"""

    def __init__(self):
        self.file_path = os.path.join(DATA_DIR, "recent_connections.json")
        os.makedirs(DATA_DIR, exist_ok=True)

    def load(self) -> list:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save(self, connections: list):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(connections, f, ensure_ascii=False, indent=2)

    def add_connection(self, ip: str, hostname: str, platform: str):
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
        connections = self.load()
        connections = [c for c in connections if c.get("ip") != ip]
        self.save(connections)


class ChatHistory:
    """聊天記錄管理"""

    def __init__(self):
        self.history_dir = os.path.join(DATA_DIR, "chat_history")
        os.makedirs(self.history_dir, exist_ok=True)

    def _get_history_file(self, peer_ip: str) -> str:
        safe_ip = peer_ip.replace(".", "_")
        return os.path.join(self.history_dir, f"chat_{safe_ip}.json")

    def load_history(self, peer_ip: str) -> list:
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
        filepath = self._get_history_file(peer_ip)
        if os.path.exists(filepath):
            os.remove(filepath)


class LanguageManager:
    """語言管理"""

    def __init__(self):
        self.settings_file = os.path.join(DATA_DIR, "settings.json")
        self.current_lang = self._load_language()

    def _load_language(self) -> str:
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get("language", "zh-TW")
            except:
                pass
        return "zh-TW"

    def save_language(self, lang: str):
        os.makedirs(DATA_DIR, exist_ok=True)
        settings = {}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except:
                pass
        settings["language"] = lang
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        self.current_lang = lang

    def get(self, key: str, **kwargs) -> str:
        text = LANG.get(self.current_lang, LANG["zh-TW"]).get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except:
                return text
        return text

    def toggle(self) -> str:
        new_lang = "en" if self.current_lang == "zh-TW" else "zh-TW"
        self.save_language(new_lang)
        return new_lang


class DiagnosticSystem:
    """診斷系統"""

    def __init__(self, lang_mgr: LanguageManager):
        import platform
        self.system = platform.system()
        self.hostname = get_hostname()
        self.local_ip = get_local_ip()
        self.lang = lang_mgr

    def run_full_diagnostic(self, target_ip: str = None, callback=None):
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
        import platform
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": self.hostname,
            "python_version": platform.python_version()
        }

    def _get_network_info(self) -> dict:
        return {
            "local_ip": self.local_ip,
            "hostname": self.hostname,
            "discovery_port": 52525,
            "transfer_port": 52526
        }

    def _check_ports(self) -> dict:
        import socket
        results = {
            "udp_52525": False,
            "tcp_52526": False,
            "udp_52525_note": "",
            "tcp_52526_note": ""
        }

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 52525))
            sock.close()
            results["udp_52525"] = True
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                results["udp_52525"] = True
                results["udp_52525_note"] = self.lang.get("pcpcs_listening")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 52526))
            sock.close()
            results["tcp_52526"] = True
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                results["tcp_52526"] = True
                results["tcp_52526_note"] = self.lang.get("pcpcs_listening")

        return results

    def _check_firewall(self) -> dict:
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
        import subprocess
        import socket

        result = {
            "ping": False,
            "ping_ms": None,
            "tcp_52526": False
        }

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
        recommendations = []

        fw = results.get("firewall_status", {})
        if fw.get("status") == "enabled":
            if fw.get("pcpcs_allowed") == "no":
                if self.system == "Linux":
                    recommendations.append({
                        "issue": self.lang.get("issue_linux_fw"),
                        "solution": self.lang.get("solution_linux_fw"),
                        "commands": [
                            "sudo ufw allow 52525/udp",
                            "sudo ufw allow 52526/tcp"
                        ]
                    })
                elif self.system == "Windows":
                    recommendations.append({
                        "issue": self.lang.get("issue_win_fw"),
                        "solution": self.lang.get("solution_win_fw"),
                        "commands": [
                            "netsh advfirewall firewall add rule name=\"PCPCS UDP\" dir=in action=allow protocol=UDP localport=52525",
                            "netsh advfirewall firewall add rule name=\"PCPCS TCP\" dir=in action=allow protocol=TCP localport=52526"
                        ]
                    })

        conn = results.get("connectivity", {})
        if conn:
            if not conn.get("ping"):
                recommendations.append({
                    "issue": self.lang.get("issue_no_ping"),
                    "solution": self.lang.get("solution_no_ping"),
                    "commands": []
                })
            elif conn.get("ping") and not conn.get("tcp_52526"):
                recommendations.append({
                    "issue": self.lang.get("issue_tcp_fail"),
                    "solution": self.lang.get("solution_tcp_fail"),
                    "commands": []
                })

        if not recommendations:
            recommendations.append({
                "issue": self.lang.get("issue_none"),
                "solution": self.lang.get("solution_none"),
                "commands": []
            })

        return recommendations

    def get_quick_setup_guide(self) -> str:
        L = self.lang
        guide = f"""
╔══════════════════════════════════════════════════════════════╗
║              {L.get("quick_setup_guide"):<43}║
╠══════════════════════════════════════════════════════════════╣
║ {L.get("local_info_label"):<60} ║
║   {L.get("computer_name")}: {self.hostname:<42} ║
║   {L.get("ip_address")}:  {self.local_ip:<43} ║
║   {L.get("operating_system")}: {self.system:<44} ║
╠══════════════════════════════════════════════════════════════╣
║ {L.get("ports_to_open"):<60} ║
║   UDP 52525 - {L.get("node_discovery"):<45} ║
║   TCP 52526 - {L.get("file_text_transfer"):<45} ║
╠══════════════════════════════════════════════════════════════╣
"""
        if self.system == "Linux":
            guide += f"""║ {L.get("linux_firewall"):<60} ║
║   sudo ufw allow 52525/udp                                    ║
║   sudo ufw allow 52526/tcp                                    ║
╚══════════════════════════════════════════════════════════════╝
"""
        elif self.system == "Windows":
            guide += f"""║ {L.get("windows_firewall"):<60} ║
║   {L.get("win_fw_step1"):<57} ║
║   {L.get("win_fw_step2"):<57} ║
║   {L.get("win_fw_step3"):<57} ║
╚══════════════════════════════════════════════════════════════╝
"""
        else:
            guide += """╚══════════════════════════════════════════════════════════════╝
"""
        return guide


class PCPCSApp:
    """PCPCS 主應用程式"""

    def __init__(self):
        self.root = tk.Tk()

        # 語言管理
        self.lang_mgr = LanguageManager()

        self.root.title(f"PCPCS - Perspic Cross PC Communication System | {get_hostname()} ({get_local_ip()})")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        self.root.configure(bg=COLORS["bg_light"])

        # 設定樣式
        self.style = ttk.Style()
        self._setup_styles()

        # Logo (使用 tkinter 原生 PhotoImage)
        self.logo_image = None
        self._load_logo()

        # 聊天記錄管理
        self.chat_history = ChatHistory()
        self.recent_connections = RecentConnections()

        # 診斷系統
        self.diagnostic = DiagnosticSystem(self.lang_mgr)

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

        # UI 元件引用 (for language switch)
        self.ui_elements = {}

        # 建立 UI
        self._create_ui()

        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_logo(self):
        """載入 Logo (使用 tkinter 原生 PhotoImage)"""
        try:
            logo_path = os.path.join(ASSETS_DIR, "logo.png")
            if os.path.exists(logo_path):
                # 使用 tkinter 原生 PhotoImage
                self.logo_image = tk.PhotoImage(file=logo_path)
                # 縮小 (subsample)
                self.logo_image = self.logo_image.subsample(5, 5)
        except Exception as e:
            print(f"Cannot load logo: {e}")
            self.logo_image = None

    def _setup_styles(self):
        """設定 UI 樣式"""
        self.style.theme_use('clam')

        self.style.configure('Main.TFrame', background=COLORS["bg_light"])
        self.style.configure('Card.TFrame', background=COLORS["bg_card"])

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

        self.style.configure('Info.TLabel',
                           background=COLORS["bg_card"],
                           foreground=COLORS["text_secondary"],
                           font=('Consolas', 9))

        self.style.configure('Card.TLabelframe',
                           background=COLORS["bg_card"],
                           foreground=COLORS["text_primary"],
                           borderwidth=1,
                           relief='solid')
        self.style.configure('Card.TLabelframe.Label',
                           background=COLORS["bg_card"],
                           foreground=COLORS["primary"],
                           font=('Segoe UI', 10, 'bold'))

        self.style.configure('Primary.TButton',
                           background=COLORS["primary"],
                           foreground='white',
                           font=('Segoe UI', 9, 'bold'),
                           padding=(10, 5))
        self.style.map('Primary.TButton',
                      background=[('active', COLORS["primary_hover"])])

        self.style.configure('Secondary.TButton',
                           background=COLORS["bg_white"],
                           foreground=COLORS["text_primary"],
                           font=('Segoe UI', 9),
                           padding=(8, 4))
        self.style.map('Secondary.TButton',
                      background=[('active', COLORS["primary_light"])])

        self.style.configure('Blue.Horizontal.TProgressbar',
                           background=COLORS["primary"],
                           troughcolor=COLORS["border"])

    def _t(self, key: str, **kwargs) -> str:
        """取得翻譯文字"""
        return self.lang_mgr.get(key, **kwargs)

    def _create_ui(self):
        """建立使用者介面"""
        L = self._t

        # 主框架
        main_frame = ttk.Frame(self.root, padding="10", style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側
        left_frame = ttk.Frame(main_frame, width=280, style='Main.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        # Logo
        if self.logo_image:
            logo_label = tk.Label(left_frame, image=self.logo_image, bg=COLORS["bg_light"])
            logo_label.pack(pady=(0, 10))

        # 語言切換按鈕
        lang_frame = ttk.Frame(left_frame, style='Main.TFrame')
        lang_frame.pack(fill=tk.X, pady=(0, 10))

        self.lang_btn = ttk.Button(
            lang_frame,
            text=L("switch_to_en") if self.lang_mgr.current_lang == "zh-TW" else L("switch_to_zh"),
            command=self._switch_language,
            style='Secondary.TButton'
        )
        self.lang_btn.pack(fill=tk.X)

        # 節點列表
        self.peer_labelframe = ttk.LabelFrame(left_frame, text=f"  {L('discovered_computers')}  ",
                                              padding="8", style='Card.TLabelframe')
        self.peer_labelframe.pack(fill=tk.BOTH, expand=True)

        list_container = tk.Frame(self.peer_labelframe, bg=COLORS["bg_white"],
                                 highlightthickness=1, highlightbackground=COLORS["border"])
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

        # 按鈕
        btn_frame = ttk.Frame(self.peer_labelframe, style='Card.TFrame')
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        self.btn_rescan = ttk.Button(btn_frame, text=L("rescan"), command=self._refresh_peers,
                                    style='Secondary.TButton')
        self.btn_rescan.pack(fill=tk.X, pady=2)

        self.btn_add_ip = ttk.Button(btn_frame, text=L("manual_add_ip"), command=self._manual_add_ip,
                                    style='Secondary.TButton')
        self.btn_add_ip.pack(fill=tk.X, pady=2)

        self.btn_test = ttk.Button(btn_frame, text=L("test_connection"), command=self._manual_ping,
                                  style='Secondary.TButton')
        self.btn_test.pack(fill=tk.X, pady=2)

        self.btn_diag = ttk.Button(btn_frame, text=L("network_diagnostic"), command=self._show_diagnostic,
                                  style='Secondary.TButton')
        self.btn_diag.pack(fill=tk.X, pady=2)

        # 最近連線
        self.recent_labelframe = ttk.LabelFrame(left_frame, text=f"  {L('recent_connections')}  ",
                                                padding="8", style='Card.TLabelframe')
        self.recent_labelframe.pack(fill=tk.X, pady=(10, 0))

        recent_container = tk.Frame(self.recent_labelframe, bg=COLORS["bg_white"],
                                   highlightthickness=1, highlightbackground=COLORS["border"])
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
        self.info_labelframe = ttk.LabelFrame(left_frame, text=f"  {L('local_info')}  ",
                                             padding="8", style='Card.TLabelframe')
        self.info_labelframe.pack(fill=tk.X, pady=(10, 0))

        self.info_labels = []
        info_texts = [
            f"{L('name')}: {get_hostname()}",
            f"{L('ip')}: {get_local_ip()}",
            f"{L('discovery_port')}: UDP 52525",
            f"{L('transfer_port')}: TCP 52526"
        ]
        for text in info_texts:
            lbl = ttk.Label(self.info_labelframe, text=text, style='Info.TLabel')
            lbl.pack(anchor='w')
            self.info_labels.append(lbl)

        # 右側
        right_frame = ttk.Frame(main_frame, style='Main.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 對話對象
        target_frame = ttk.Frame(right_frame, style='Main.TFrame')
        target_frame.pack(fill=tk.X, pady=(0, 8))

        self.target_title = ttk.Label(target_frame, text=L("chat_target"), style='Title.TLabel')
        self.target_title.pack(side=tk.LEFT)

        self.target_label = ttk.Label(target_frame, text=L("select_computer"), style='Subtitle.TLabel')
        self.target_label.pack(side=tk.LEFT, padx=(10, 0))

        # 對話框
        self.chat_labelframe = ttk.LabelFrame(right_frame, text=f"  {L('conversation')}  ",
                                             padding="8", style='Card.TLabelframe')
        self.chat_labelframe.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        chat_container = tk.Frame(self.chat_labelframe, bg=COLORS["bg_white"],
                                 highlightthickness=1, highlightbackground=COLORS["border"])
        chat_container.pack(fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_container, height=15, font=('Consolas', 10),
            state='disabled', wrap=tk.WORD,
            bg=COLORS["bg_white"], fg=COLORS["text_primary"],
            borderwidth=0, highlightthickness=0
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.chat_display.tag_configure('self', foreground=COLORS["success"], font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('peer', foreground=COLORS["primary"], font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('system', foreground=COLORS["text_secondary"], font=('Consolas', 9, 'italic'))
        self.chat_display.tag_configure('file', foreground='#7C3AED', font=('Consolas', 10))
        self.chat_display.tag_configure('timestamp', foreground=COLORS["text_secondary"], font=('Consolas', 8))

        # 輸入區
        input_frame = ttk.Frame(self.chat_labelframe, style='Card.TFrame')
        input_frame.pack(fill=tk.X, pady=(8, 0))

        input_container = tk.Frame(input_frame, bg=COLORS["bg_white"],
                                  highlightthickness=1, highlightbackground=COLORS["border"])
        input_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.message_input = tk.Entry(
            input_container, font=('Segoe UI', 11),
            bg=COLORS["bg_white"], fg=COLORS["text_primary"],
            borderwidth=0, highlightthickness=0
        )
        self.message_input.pack(fill=tk.X, padx=8, pady=6)
        self.message_input.bind('<Return>', lambda e: self._send_text())

        self.send_btn = ttk.Button(input_frame, text=L("send"), command=self._send_text,
                                  width=8, style='Primary.TButton')
        self.send_btn.pack(side=tk.LEFT)

        # 聊天控制
        chat_btn_frame = ttk.Frame(self.chat_labelframe, style='Card.TFrame')
        chat_btn_frame.pack(fill=tk.X, pady=(8, 0))

        self.btn_clear = ttk.Button(chat_btn_frame, text=L("clear_history"),
                                   command=self._clear_chat_history, style='Secondary.TButton')
        self.btn_clear.pack(side=tk.LEFT)

        self.btn_open_folder = ttk.Button(chat_btn_frame, text=L("open_data_folder"),
                                         command=self._open_data_folder, style='Secondary.TButton')
        self.btn_open_folder.pack(side=tk.LEFT, padx=8)

        # 檔案傳輸
        self.file_labelframe = ttk.LabelFrame(right_frame, text=f"  {L('file_transfer')}  ",
                                             padding="8", style='Card.TLabelframe')
        self.file_labelframe.pack(fill=tk.X, pady=(0, 10))

        file_select_frame = ttk.Frame(self.file_labelframe, style='Card.TFrame')
        file_select_frame.pack(fill=tk.X)

        file_entry_container = tk.Frame(file_select_frame, bg=COLORS["bg_white"],
                                       highlightthickness=1, highlightbackground=COLORS["border"])
        file_entry_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(
            file_entry_container, textvariable=self.file_path_var,
            font=('Consolas', 10),
            bg=COLORS["bg_white"], fg=COLORS["text_primary"],
            borderwidth=0, highlightthickness=0
        )
        self.file_entry.pack(fill=tk.X, padx=6, pady=4)

        self.btn_browse = ttk.Button(file_select_frame, text=L("select"), command=self._browse_file,
                                    style='Secondary.TButton')
        self.btn_browse.pack(side=tk.LEFT, padx=(0, 8))

        self.send_file_btn = ttk.Button(file_select_frame, text=L("send_file"),
                                       command=self._send_file, style='Primary.TButton')
        self.send_file_btn.pack(side=tk.LEFT)

        # 進度條
        progress_frame = ttk.Frame(self.file_labelframe, style='Card.TFrame')
        progress_frame.pack(fill=tk.X, pady=(8, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100,
                                           style='Blue.Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(progress_frame, text="", style='Info.TLabel')
        self.progress_label.pack(anchor='w', pady=(4, 0))

        # 系統日誌
        self.log_labelframe = ttk.LabelFrame(right_frame, text=f"  {L('system_log')}  ",
                                            padding="8", style='Card.TLabelframe')
        self.log_labelframe.pack(fill=tk.X)

        log_container = tk.Frame(self.log_labelframe, bg=COLORS["bg_white"],
                                highlightthickness=1, highlightbackground=COLORS["border"])
        log_container.pack(fill=tk.X)

        self.log_text = scrolledtext.ScrolledText(
            log_container, height=4, font=('Consolas', 8),
            state='disabled', wrap=tk.WORD,
            bg=COLORS["bg_white"], fg=COLORS["text_secondary"],
            borderwidth=0, highlightthickness=0
        )
        self.log_text.pack(fill=tk.X, padx=2, pady=2)

    def _switch_language(self):
        """切換語言並自動重啟"""
        new_lang = self.lang_mgr.toggle()

        # 自動重啟應用程式
        self._restart_app()

    def _restart_app(self):
        """重啟應用程式"""
        # 停止所有服務
        try:
            self.discovery.stop()
            self.server.stop()
        except:
            pass

        # 關閉視窗
        self.root.destroy()

        # 重新啟動 Python 程式
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def _update_recent_list(self):
        self.recent_listbox.delete(0, tk.END)
        for conn in self.recent_connections.load()[:5]:
            hostname = conn.get("hostname", "Unknown")
            ip = conn.get("ip", "")
            self.recent_listbox.insert(tk.END, f"{hostname} ({ip})")

    def _on_recent_double_click(self, event):
        selection = self.recent_listbox.curselection()
        if selection:
            connections = self.recent_connections.load()
            if selection[0] < len(connections):
                conn = connections[selection[0]]
                ip = conn.get("ip")
                hostname = conn.get("hostname")
                platform_name = conn.get("platform", "Unknown")

                if ip not in self.discovery.peers:
                    peer = PeerInfo(ip, hostname, platform_name)
                    self.discovery.peers[ip] = peer
                    self._update_peer_list(self.discovery.peers)

                self.selected_peer_ip = ip
                self.selected_peer_name = hostname
                self.target_label.config(text=f"{hostname} ({ip})")
                self._load_chat_history()

                for i in range(self.peer_listbox.size()):
                    if ip in self.peer_listbox.get(i):
                        self.peer_listbox.selection_clear(0, tk.END)
                        self.peer_listbox.selection_set(i)
                        break

                self._log(self._t("selected_recent", name=hostname))

    def _on_peer_update(self, peers: dict):
        self.root.after(0, lambda: self._update_peer_list(peers))

    def _update_peer_list(self, peers: dict):
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
                self._log(self._t("selected", name=self.selected_peer_name))
                self._load_chat_history()

                if self.selected_peer_ip in self.discovery.peers:
                    peer = self.discovery.peers[self.selected_peer_ip]
                    self.recent_connections.add_connection(
                        self.selected_peer_ip,
                        self.selected_peer_name,
                        peer.platform
                    )
                    self._update_recent_list()

    def _ensure_peer_exists(self, sender_ip: str, sender_name: str, sender_platform: str):
        if sender_ip not in self.discovery.peers:
            peer = PeerInfo(sender_ip, sender_name, sender_platform)
            peer.is_reachable = True
            self.discovery.peers[sender_ip] = peer
            self.root.after(0, lambda: self._update_peer_list(self.discovery.peers))
            self._log(self._t("auto_add_peer", name=sender_name, ip=sender_ip))

    def _load_chat_history(self):
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
                self.chat_display.insert(tk.END, f"  {sender} ({self._t('me')}): ", 'self')
            else:
                self.chat_display.insert(tk.END, f"  {sender}: ", 'peer')

            if is_file:
                file_info = entry.get("file_info", {})
                size_str = self._format_size(file_info.get("size", 0))
                speed_str = file_info.get("speed", "")
                self.chat_display.insert(tk.END, f"{self._t('file_label')} {message} ({size_str}) {speed_str}\n", 'file')
            else:
                self.chat_display.insert(tk.END, f"{message}\n", '')

            self.chat_display.insert(tk.END, "\n", '')

        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def _add_chat_message(self, sender: str, message: str, is_file: bool = False, file_info: dict = None):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"[{timestamp}]\n", 'timestamp')

        if sender == get_hostname():
            self.chat_display.insert(tk.END, f"  {sender} ({self._t('me')}): ", 'self')
        else:
            self.chat_display.insert(tk.END, f"  {sender}: ", 'peer')

        if is_file:
            size_str = self._format_size(file_info.get("size", 0)) if file_info else ""
            speed_str = file_info.get("speed", "") if file_info else ""
            self.chat_display.insert(tk.END, f"{self._t('file_label')} {message} ({size_str}) {speed_str}\n", 'file')
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
        if not self.selected_peer_ip:
            messagebox.showwarning(self._t("hint"), self._t("select_chat_target"))
            return

        result = messagebox.askyesno(
            self._t("confirm_clear"),
            self._t("confirm_clear_msg", name=self.selected_peer_name)
        )

        if result:
            self.chat_history.clear_history(self.selected_peer_ip)
            self.chat_display.config(state='normal')
            self.chat_display.delete('1.0', tk.END)
            self.chat_display.config(state='disabled')
            self._log(self._t("history_cleared"))

    def _open_data_folder(self):
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
        self._log(self._t("scanning"))
        self.discovery.peers.clear()
        self._update_peer_list({})

    def _manual_ping(self):
        if not self.selected_peer_ip:
            messagebox.showwarning(self._t("hint"), self._t("select_target_first"))
            return

        self._log(self._t("pinging", ip=self.selected_peer_ip))

        def do_ping():
            result = self.discovery.manual_ping(self.selected_peer_ip)
            if result:
                self._log(self._t("ping_success", ip=self.selected_peer_ip, ms=result))
            else:
                self._log(self._t("ping_fail", ip=self.selected_peer_ip))

        threading.Thread(target=do_ping, daemon=True).start()

    def _manual_add_ip(self):
        ip = simpledialog.askstring(self._t("manual_add_title"), self._t("enter_ip"), parent=self.root)

        if ip and ip.strip():
            ip = ip.strip()
            self._log(self._t("trying_connect", ip=ip))

            def try_connect():
                ping_result = self.discovery.manual_ping(ip)
                hostname = f"Manual-{ip}"
                platform_name = "Unknown"

                peer = PeerInfo(ip, hostname, platform_name)
                peer.ping_ms = ping_result
                peer.is_reachable = ping_result is not None
                self.discovery.peers[ip] = peer

                if ping_result:
                    self._log(self._t("add_success", ip=ip, ms=ping_result))
                else:
                    self._log(self._t("add_no_ping", ip=ip))

                def select_peer():
                    self._update_peer_list(self.discovery.peers)
                    self.selected_peer_ip = ip
                    self.selected_peer_name = hostname
                    self.target_label.config(text=f"{hostname} ({ip})")
                    self._load_chat_history()

                    for i in range(self.peer_listbox.size()):
                        if ip in self.peer_listbox.get(i):
                            self.peer_listbox.selection_clear(0, tk.END)
                            self.peer_listbox.selection_set(i)
                            break

                self.root.after(0, select_peer)

            threading.Thread(target=try_connect, daemon=True).start()

    def _show_diagnostic(self):
        L = self._t
        diag_window = tk.Toplevel(self.root)
        diag_window.title(L("diagnostic_title"))
        diag_window.geometry("700x550")
        diag_window.transient(self.root)
        diag_window.configure(bg=COLORS["bg_light"])

        result_container = tk.Frame(diag_window, bg=COLORS["bg_white"],
                                   highlightthickness=1, highlightbackground=COLORS["border"])
        result_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        result_text = scrolledtext.ScrolledText(
            result_container, font=('Consolas', 10),
            bg=COLORS["bg_white"], fg=COLORS["text_primary"],
            borderwidth=0, highlightthickness=0
        )
        result_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        guide = self.diagnostic.get_quick_setup_guide()
        result_text.insert(tk.END, guide)
        result_text.insert(tk.END, f"\n\n{L('diagnostic_running')}\n")

        btn_frame = ttk.Frame(diag_window, style='Main.TFrame')
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def run_diagnostic():
            result_text.delete('1.0', tk.END)
            result_text.insert(tk.END, guide)
            result_text.insert(tk.END, f"\n\n{L('diagnostic_running')}\n")
            result_text.update()

            target = self.selected_peer_ip

            def on_complete(results):
                diag_window.after(0, lambda: show_results(results))

            def show_results(results):
                result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
                result_text.insert(tk.END, f"{L('diagnostic_result')}\n")
                result_text.insert(tk.END, "=" * 60 + "\n\n")

                sys_info = results.get("system_info", {})
                result_text.insert(tk.END, f"{L('os_label')}: {sys_info.get('os', 'Unknown')} {sys_info.get('os_version', '')[:30]}\n")

                ports = results.get("port_status", {})
                result_text.insert(tk.END, f"\n{L('port_status')}:\n")
                udp_status = L('available') if ports.get('udp_52525') else L('unavailable')
                tcp_status = L('available') if ports.get('tcp_52526') else L('unavailable')
                udp_note = f" ({ports.get('udp_52525_note', '')})" if ports.get('udp_52525_note') else ""
                tcp_note = f" ({ports.get('tcp_52526_note', '')})" if ports.get('tcp_52526_note') else ""
                result_text.insert(tk.END, f"  UDP 52525: {udp_status}{udp_note}\n")
                result_text.insert(tk.END, f"  TCP 52526: {tcp_status}{tcp_note}\n")

                fw = results.get("firewall_status", {})
                result_text.insert(tk.END, f"\n{L('firewall')}: {fw.get('status', 'unknown')}\n")

                conn = results.get("connectivity")
                if conn:
                    result_text.insert(tk.END, f"\n{L('connection_test')} ({target}):\n")
                    ping_status = L('success') if conn.get('ping') else L('fail')
                    result_text.insert(tk.END, f"  {L('ping_label')}: {ping_status}")
                    if conn.get('ping_ms'):
                        result_text.insert(tk.END, f" ({conn['ping_ms']:.1f}ms)")
                    tcp_status = L('connected') if conn.get('tcp_52526') else L('not_connected')
                    result_text.insert(tk.END, f"\n  TCP 52526: {tcp_status}\n")

                result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
                result_text.insert(tk.END, f"{L('recommendations')}:\n")
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

        ttk.Button(btn_frame, text=L("re_diagnose"), command=run_diagnostic,
                  style='Secondary.TButton').pack(side=tk.LEFT)
        ttk.Button(btn_frame, text=L("copy_info"),
                  command=lambda: self._copy_to_clipboard(result_text.get('1.0', tk.END)),
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text=L("close"), command=diag_window.destroy,
                  style='Primary.TButton').pack(side=tk.RIGHT)

        diag_window.after(100, run_diagnostic)

    def _copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo(self._t("hint"), self._t("copied"))

    def _browse_file(self):
        filepath = filedialog.askopenfilename(title=self._t("select_file_title"))
        if filepath:
            self.file_path_var.set(filepath)

    def _send_text(self):
        if not self.selected_peer_ip:
            messagebox.showwarning(self._t("hint"), self._t("select_target_first"))
            return

        text = self.message_input.get().strip()
        if not text:
            return

        self.message_input.delete(0, tk.END)
        self._add_chat_message(get_hostname(), text)
        self._log(self._t("sending_text"))
        self.send_btn.config(state='disabled')
        self.client.send_text(self.selected_peer_ip, text)

    def _send_file(self):
        if not self.selected_peer_ip:
            messagebox.showwarning(self._t("hint"), self._t("select_target_first"))
            return

        filepath = self.file_path_var.get()
        if not filepath or not os.path.exists(filepath):
            messagebox.showwarning(self._t("hint"), self._t("select_valid_file"))
            return

        self.transfer_size = os.path.getsize(filepath)
        self.transfer_start_time = time.time()

        self._log(self._t("sending_file"))
        self.send_file_btn.config(state='disabled')
        self.progress_var.set(0)
        self.client.send_file(self.selected_peer_ip, filepath)

    def _on_send_progress(self, progress: float, message: str):
        self.root.after(0, lambda: self._update_progress(progress, message))

    def _on_receive_progress(self, progress: float, message: str):
        self.root.after(0, lambda: self._update_progress(progress, message))

    def _update_progress(self, progress: float, message: str):
        self.progress_var.set(progress)

        speed_str = ""
        if self.transfer_start_time and self.transfer_size > 0:
            elapsed = time.time() - self.transfer_start_time
            if elapsed > 0:
                speed = (progress / 100 * self.transfer_size) / elapsed
                speed_str = f" | {self._format_size(speed)}/s"

        self.progress_label.config(text=f"{message} ({progress:.1f}%){speed_str}")

    def _on_send_complete(self, success: bool, message: str):
        self.root.after(0, lambda: self._handle_send_complete(success, message))

    def _handle_send_complete(self, success: bool, message: str):
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
            self._log(f"{self._t('send_success')} {speed_str}")
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
            self._log(self._t("send_fail", msg=message))

        self.transfer_start_time = None
        self.transfer_size = 0

    def _on_text_received(self, sender_ip: str, sender_name: str, text: str, sender_platform: str = "Unknown"):
        self.root.after(0, lambda: self._handle_text_received(sender_ip, sender_name, text, sender_platform))

    def _handle_text_received(self, sender_ip: str, sender_name: str, text: str, sender_platform: str = "Unknown"):
        self._ensure_peer_exists(sender_ip, sender_name, sender_platform)

        if self.selected_peer_ip == sender_ip:
            self._add_chat_message(sender_name, text)
        else:
            self.chat_history.save_message(sender_ip, sender_name, text)
            self.chat_display.config(state='normal')
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
            self.chat_display.insert(tk.END, f"{self._t('new_message_from', name=sender_name, ip=sender_ip)}\n", 'system')
            self.chat_display.see(tk.END)
            self.chat_display.config(state='disabled')

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._log(self._t("received_text"))

    def _on_file_received(self, sender_ip: str, sender_name: str, filepath: str, filesize: int, sender_platform: str = "Unknown"):
        self.root.after(0, lambda: self._handle_file_received(sender_ip, sender_name, filepath, filesize, sender_platform))

    def _handle_file_received(self, sender_ip: str, sender_name: str, filepath: str, filesize: int, sender_platform: str = "Unknown"):
        self._ensure_peer_exists(sender_ip, sender_name, sender_platform)

        filename = os.path.basename(filepath)
        size_str = self._format_size(filesize)

        file_info = {"size": filesize, "path": filepath}

        if self.selected_peer_ip == sender_ip:
            self._add_chat_message(sender_name, filename, is_file=True, file_info=file_info)
        else:
            self.chat_history.save_message(sender_ip, sender_name, filename, is_file=True, file_info=file_info)

        self._log(self._t("received_file", name=filename, size=size_str))

        result = messagebox.askyesno(
            self._t("file_received_title", name=sender_name),
            self._t("file_received_msg", filename=filename, size=size_str)
        )
        if result:
            self._open_receive_folder()

    def _open_receive_folder(self):
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
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _log(self, message: str):
        def _write():
            self.log_text.config(state='normal')
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')

        self.root.after(0, _write)

    def _on_close(self):
        self.discovery.stop()
        self.server.stop()
        self.root.destroy()

    def run(self):
        self._log(self._t("starting"))
        self.discovery.start()
        self.server.start()
        self._log(self._t("service_started"))
        self._log(self._t("receive_location", path=RECEIVE_DIR))

        self.root.mainloop()


def main():
    app = PCPCSApp()
    app.run()


if __name__ == "__main__":
    main()
