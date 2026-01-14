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
        "copyright": "© 2025 Perspic AI Engineering Limited",
        "website": "perspic.net",
        "send_folder": "發送資料夾",
        "select_folder_title": "選擇要發送的資料夾",
        "select_valid_folder": "請選擇有效的資料夾",
        "sending_folder": "正在發送資料夾...",
        "folder_empty": "資料夾是空的",
        "folder_send_success": "資料夾 {name} 發送成功 ({count} 個檔案)",
        "folder_send_fail": "資料夾發送失敗: {msg}",
        "received_folder": "收到資料夾: {name} ({count} 個檔案)",
        "folder_received_title": "收到資料夾 - {name}",
        "folder_received_msg": "資料夾: {foldername}\n檔案數: {count}\n總大小: {size}\n\n是否開啟資料夾?",
        "folder_progress": "({current}/{total}) {filename}",
        "file_skipped": "已跳過 (相同檔案)",
        "cancel_transfer": "取消傳輸",
        "transfer_cancelled": "傳輸已取消",
        "reset_progress": "重置",
        "parallel_ports": "並行傳輸",
        "parallel_ports_info": "TCP 52530-52537 - 大檔案並行傳輸 (8連接)",
        "parallel_ports_status": "並行端口狀態",
        "parallel_ports_test": "並行端口連接測試",
        "ports_open": "可用",
        "issue_parallel_ports": "並行傳輸端口未開放",
        "solution_parallel_ports": "開放並行端口以啟用高速傳輸:",
        "transfer_warning": "傳輸中，請勿關閉視窗！",
        "eta_label": "預計剩餘",
        "delete_received": "刪除已接收檔案",
        "delete_received_title": "刪除已接收檔案",
        "delete_received_msg": "確定要刪除所有從 {name} 收到的檔案嗎？\n\n這將刪除：\n- 所有接收的檔案和資料夾\n- 聊天記錄\n\n此操作無法復原。",
        "delete_success": "已刪除 {count} 個檔案/資料夾",
        "delete_fail": "刪除失敗: {msg}",
        "open_receive_folder": "開啟接收資料夾",
        "diag_step_system": "收集系統資訊...",
        "diag_step_ports": "檢查端口狀態...",
        "diag_step_firewall": "檢查防火牆設定...",
        "diag_step_connectivity": "測試連接...",
        "diag_step_recommendations": "生成建議...",
        "diag_progress": "診斷進度: {step}/{total} - {msg}",
        "port_in_use": "被其他程式佔用",
        "port_used_by": "被 {app} 佔用",
        "no_firewall_detected": "未檢測到防火牆",
        "firewall_software": "防火牆軟體",
        "firewall_open_steps": "開放端口步驟:",
        "win_step1": "1. 按 Win+R，輸入 wf.msc 並回車",
        "win_step2": "2. 點擊「入站規則」→「新增規則」",
        "win_step3": "3. 選擇「端口」→ 下一步",
        "win_step4": "4. 選擇 TCP，輸入 52526,52530-52537",
        "win_step5": "5. 重複以上步驟，選擇 UDP，輸入 52525",
        "macos_step1": "系統偏好設定 → 安全性與隱私 → 防火牆",
        "macos_step2": "允許 Python 接受傳入連接",
        "version": "版本",
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
        "copyright": "© 2025 Perspic AI Engineering Limited",
        "website": "perspic.net",
        "send_folder": "Send Folder",
        "select_folder_title": "Select folder to send",
        "select_valid_folder": "Please select a valid folder",
        "sending_folder": "Sending folder...",
        "folder_empty": "Folder is empty",
        "folder_send_success": "Folder {name} sent successfully ({count} files)",
        "folder_send_fail": "Folder send failed: {msg}",
        "received_folder": "Folder received: {name} ({count} files)",
        "folder_received_title": "Folder Received - {name}",
        "folder_received_msg": "Folder: {foldername}\nFiles: {count}\nTotal size: {size}\n\nOpen the folder?",
        "folder_progress": "({current}/{total}) {filename}",
        "file_skipped": "Skipped (identical file)",
        "cancel_transfer": "Cancel Transfer",
        "transfer_cancelled": "Transfer cancelled",
        "reset_progress": "Reset",
        "parallel_ports": "Parallel Transfer",
        "parallel_ports_info": "TCP 52530-52537 - Large file parallel transfer (8 connections)",
        "parallel_ports_status": "Parallel Ports Status",
        "parallel_ports_test": "Parallel Ports Connection Test",
        "ports_open": "Open",
        "issue_parallel_ports": "Parallel transfer ports not open",
        "solution_parallel_ports": "Open parallel ports for high-speed transfer:",
        "transfer_warning": "Transfer in progress, do not close window!",
        "eta_label": "ETA",
        "delete_received": "Delete Received Files",
        "delete_received_title": "Delete Received Files",
        "delete_received_msg": "Are you sure you want to delete all files received from {name}?\n\nThis will delete:\n- All received files and folders\n- Chat history\n\nThis action cannot be undone.",
        "delete_success": "Deleted {count} files/folders",
        "delete_fail": "Delete failed: {msg}",
        "open_receive_folder": "Open Receive Folder",
        "diag_step_system": "Gathering system info...",
        "diag_step_ports": "Checking port status...",
        "diag_step_firewall": "Checking firewall settings...",
        "diag_step_connectivity": "Testing connectivity...",
        "diag_step_recommendations": "Generating recommendations...",
        "diag_progress": "Diagnostic progress: {step}/{total} - {msg}",
        "port_in_use": "In use by another app",
        "port_used_by": "Used by {app}",
        "no_firewall_detected": "No firewall detected",
        "firewall_software": "Firewall Software",
        "firewall_open_steps": "Steps to open ports:",
        "win_step1": "1. Press Win+R, type wf.msc and press Enter",
        "win_step2": "2. Click 'Inbound Rules' → 'New Rule'",
        "win_step3": "3. Select 'Port' → Next",
        "win_step4": "4. Select TCP, enter 52526,52530-52537",
        "win_step5": "5. Repeat above, select UDP, enter 52525",
        "macos_step1": "System Preferences → Security & Privacy → Firewall",
        "macos_step2": "Allow Python to accept incoming connections",
        "version": "Version",
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

    def get_received_files(self, peer_ip: str) -> list:
        """取得從該 peer 收到的所有檔案路徑"""
        history = self.load_history(peer_ip)
        received = []
        for entry in history:
            if entry.get("is_file") and entry.get("file_info"):
                file_path = entry["file_info"].get("path")
                if file_path and os.path.exists(file_path):
                    received.append(file_path)
        return received


class LanguageManager:
    """語言管理"""

    def __init__(self):
        self.settings_file = os.path.join(DATA_DIR, "settings.json")
        self.current_lang = self._load_language()

    def _load_settings(self) -> dict:
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_settings(self, settings: dict):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def get_last_selected_peer(self) -> tuple:
        """取得上次選擇的 peer"""
        settings = self._load_settings()
        return settings.get("last_peer_ip"), settings.get("last_peer_name")

    def set_last_selected_peer(self, ip: str, name: str):
        """保存當前選擇的 peer"""
        settings = self._load_settings()
        settings["last_peer_ip"] = ip
        settings["last_peer_name"] = name
        self._save_settings(settings)

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

    def run_full_diagnostic(self, target_ip: str = None, callback=None, progress_callback=None):
        """
        執行完整診斷
        progress_callback: (step, total, message) -> None
        """
        total_steps = 5 if target_ip else 4

        def report_progress(step, msg):
            if progress_callback:
                progress_callback(step, total_steps, msg)

        report_progress(1, self.lang.get("diag_step_system"))
        results = {
            "system_info": self._get_system_info(),
            "network_info": self._get_network_info(),
        }

        report_progress(2, self.lang.get("diag_step_ports"))
        results["port_status"] = self._check_ports()

        report_progress(3, self.lang.get("diag_step_firewall"))
        results["firewall_status"] = self._check_firewall()

        results["connectivity"] = None
        if target_ip:
            report_progress(4, self.lang.get("diag_step_connectivity"))
            results["connectivity"] = self._test_connectivity(target_ip)
            report_progress(5, self.lang.get("diag_step_recommendations"))
        else:
            report_progress(4, self.lang.get("diag_step_recommendations"))

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

    def _get_port_user(self, port: int, protocol: str = "tcp") -> str:
        """檢測是什麼程式在使用端口"""
        import subprocess
        try:
            if self.system == "Windows":
                # Windows 使用 netstat
                cmd = ["netstat", "-ano"]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                for line in proc.stdout.split('\n'):
                    if f":{port}" in line and protocol.upper() in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            # 獲取進程名稱
                            try:
                                proc2 = subprocess.run(
                                    ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                                    capture_output=True, text=True, timeout=5
                                )
                                if proc2.stdout.strip():
                                    name = proc2.stdout.strip().split(',')[0].strip('"')
                                    if "python" in name.lower() or "PCPCS" in name:
                                        return "PCPCS"
                                    return name
                            except:
                                return f"PID:{pid}"
            else:
                # Linux/macOS 使用 lsof
                proto_flag = "-i" if protocol == "tcp" else "-iUDP"
                cmd = ["lsof", f"-i:{port}"]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                for line in proc.stdout.split('\n')[1:]:  # 跳過標題行
                    if line.strip():
                        parts = line.split()
                        if parts:
                            name = parts[0]
                            if "python" in name.lower():
                                return "PCPCS"
                            return name
        except:
            pass
        return ""

    def _check_ports(self) -> dict:
        import socket
        results = {
            "udp_52525": False,
            "tcp_52526": False,
            "udp_52525_note": "",
            "tcp_52526_note": "",
            "udp_52525_user": "",
            "tcp_52526_user": "",
            "parallel_ports": [],  # 並行端口狀態列表
            "parallel_ports_ok": 0,
            "parallel_ports_total": 8
        }

        # 檢查 UDP 52525
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 52525))
            sock.close()
            results["udp_52525"] = True
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                user = self._get_port_user(52525, "udp")
                if user == "PCPCS" or not user:
                    results["udp_52525"] = True
                    results["udp_52525_note"] = self.lang.get("pcpcs_listening")
                else:
                    results["udp_52525"] = False
                    results["udp_52525_note"] = self.lang.get("port_in_use")
                    results["udp_52525_user"] = user

        # 檢查 TCP 52526
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 52526))
            sock.close()
            results["tcp_52526"] = True
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                user = self._get_port_user(52526, "tcp")
                if user == "PCPCS" or not user:
                    results["tcp_52526"] = True
                    results["tcp_52526_note"] = self.lang.get("pcpcs_listening")
                else:
                    results["tcp_52526"] = False
                    results["tcp_52526_note"] = self.lang.get("port_in_use")
                    results["tcp_52526_user"] = user

        # 檢查並行傳輸端口 52530-52537
        for port in range(52530, 52538):
            port_ok = False
            port_user = ""
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('', port))
                sock.close()
                port_ok = True
            except OSError as e:
                if "Address already in use" in str(e) or "Only one usage" in str(e):
                    user = self._get_port_user(port, "tcp")
                    if user == "PCPCS" or not user:
                        port_ok = True
                    else:
                        port_user = user
            results["parallel_ports"].append({"port": port, "ok": port_ok, "user": port_user})
            if port_ok:
                results["parallel_ports_ok"] += 1

        return results

    def _check_firewall(self) -> dict:
        import subprocess
        result = {
            "status": "unknown",
            "software": "",  # 防火牆軟體名稱
            "details": "",
            "pcpcs_allowed": "unknown",
            "open_steps": []  # 開放端口的步驟
        }

        try:
            if self.system == "Windows":
                result["software"] = "Windows Defender Firewall"
                proc = subprocess.run(
                    ["netsh", "advfirewall", "show", "allprofiles", "state"],
                    capture_output=True, text=True, timeout=10
                )
                result["details"] = proc.stdout
                if "ON" in proc.stdout:
                    result["status"] = "enabled"
                    # 檢查 PCPCS 規則是否存在
                    try:
                        proc2 = subprocess.run(
                            ["netsh", "advfirewall", "firewall", "show", "rule", "name=all"],
                            capture_output=True, text=True, timeout=15
                        )
                        if "PCPCS" in proc2.stdout or ("52525" in proc2.stdout and "52526" in proc2.stdout):
                            result["pcpcs_allowed"] = "yes"
                        else:
                            result["pcpcs_allowed"] = "no"
                    except:
                        result["pcpcs_allowed"] = "unknown"

                    # Windows 開放端口步驟
                    result["open_steps"] = [
                        self.lang.get("win_step1"),
                        self.lang.get("win_step2"),
                        self.lang.get("win_step3"),
                        self.lang.get("win_step4"),
                        self.lang.get("win_step5"),
                    ]
                else:
                    result["status"] = "disabled"

            elif self.system == "Linux":
                # 檢測使用的防火牆軟體
                fw_detected = False

                # 檢查 ufw
                try:
                    proc = subprocess.run(
                        ["ufw", "status"],
                        capture_output=True, text=True, timeout=10
                    )
                    if proc.returncode == 0:
                        result["software"] = "UFW (Uncomplicated Firewall)"
                        result["details"] = proc.stdout
                        fw_detected = True
                        if "active" in proc.stdout.lower():
                            result["status"] = "enabled"
                            if "52525" in proc.stdout and "52526" in proc.stdout:
                                result["pcpcs_allowed"] = "yes"
                            else:
                                result["pcpcs_allowed"] = "no"
                            result["open_steps"] = [
                                "sudo ufw allow 52525/udp",
                                "sudo ufw allow 52526/tcp",
                                "sudo ufw allow 52530:52537/tcp",
                                "sudo ufw reload"
                            ]
                        else:
                            result["status"] = "disabled"
                except FileNotFoundError:
                    pass

                # 檢查 firewalld
                if not fw_detected:
                    try:
                        proc = subprocess.run(
                            ["firewall-cmd", "--state"],
                            capture_output=True, text=True, timeout=10
                        )
                        if proc.returncode == 0 and "running" in proc.stdout.lower():
                            result["software"] = "firewalld"
                            result["status"] = "enabled"
                            fw_detected = True
                            result["open_steps"] = [
                                "sudo firewall-cmd --add-port=52525/udp --permanent",
                                "sudo firewall-cmd --add-port=52526/tcp --permanent",
                                "sudo firewall-cmd --add-port=52530-52537/tcp --permanent",
                                "sudo firewall-cmd --reload"
                            ]
                    except FileNotFoundError:
                        pass

                # 檢查 iptables
                if not fw_detected:
                    try:
                        proc = subprocess.run(
                            ["iptables", "-L", "-n"],
                            capture_output=True, text=True, timeout=10
                        )
                        if proc.returncode == 0:
                            result["software"] = "iptables"
                            # 檢查是否有規則
                            if "DROP" in proc.stdout or "REJECT" in proc.stdout:
                                result["status"] = "enabled"
                            else:
                                result["status"] = "minimal"
                            fw_detected = True
                            result["open_steps"] = [
                                "sudo iptables -A INPUT -p udp --dport 52525 -j ACCEPT",
                                "sudo iptables -A INPUT -p tcp --dport 52526 -j ACCEPT",
                                "sudo iptables -A INPUT -p tcp --dport 52530:52537 -j ACCEPT"
                            ]
                    except (FileNotFoundError, PermissionError):
                        pass

                if not fw_detected:
                    result["software"] = self.lang.get("no_firewall_detected")
                    result["status"] = "unknown"

            elif self.system == "Darwin":  # macOS
                result["software"] = "macOS Firewall"
                try:
                    proc = subprocess.run(
                        ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
                        capture_output=True, text=True, timeout=10
                    )
                    if "enabled" in proc.stdout.lower():
                        result["status"] = "enabled"
                    else:
                        result["status"] = "disabled"
                except:
                    pass
                result["open_steps"] = [
                    self.lang.get("macos_step1"),
                    self.lang.get("macos_step2"),
                ]

        except Exception as e:
            result["error"] = str(e)

        return result

    def _test_connectivity(self, target_ip: str) -> dict:
        import subprocess
        import socket

        result = {
            "ping": False,
            "ping_ms": None,
            "tcp_52526": False,
            "parallel_ports_ok": 0,
            "parallel_ports_total": 8,
            "parallel_ports_detail": []
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

        # 測試並行傳輸端口 52530-52537 連接
        for port in range(52530, 52538):
            port_ok = False
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((target_ip, port))
                sock.close()
                port_ok = True
            except:
                pass
            result["parallel_ports_detail"].append({"port": port, "ok": port_ok})
            if port_ok:
                result["parallel_ports_ok"] += 1

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
            # 檢查並行端口連接
            elif conn.get("tcp_52526") and conn.get("parallel_ports_ok", 0) < 8:
                if self.system == "Linux":
                    recommendations.append({
                        "issue": self.lang.get("issue_parallel_ports"),
                        "solution": self.lang.get("solution_parallel_ports"),
                        "commands": ["sudo ufw allow 52530:52537/tcp"]
                    })
                elif self.system == "Windows":
                    recommendations.append({
                        "issue": self.lang.get("issue_parallel_ports"),
                        "solution": self.lang.get("solution_parallel_ports"),
                        "commands": [
                            "netsh advfirewall firewall add rule name=\"PCPCS Parallel\" dir=in action=allow protocol=TCP localport=52530-52537"
                        ]
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

        lines = [
            "━" * 50,
            f"  {L.get('quick_setup_guide')}",
            "━" * 50,
            "",
            f"▸ {L.get('local_info_label')}",
            f"    {L.get('computer_name')}: {self.hostname}",
            f"    {L.get('ip_address')}: {self.local_ip}",
            f"    {L.get('operating_system')}: {self.system}",
            "",
            f"▸ {L.get('ports_to_open')}",
            f"    UDP 52525 - {L.get('node_discovery')}",
            f"    TCP 52526 - {L.get('file_text_transfer')}",
            f"    TCP 52530-52537 - {L.get('parallel_ports')}",
            "",
        ]

        if self.system == "Linux":
            lines.extend([
                f"▸ {L.get('linux_firewall')}",
                "    sudo ufw allow 52525/udp",
                "    sudo ufw allow 52526/tcp",
                "    sudo ufw allow 52530:52537/tcp",
            ])
        elif self.system == "Windows":
            lines.extend([
                f"▸ {L.get('windows_firewall')}",
                f"    {L.get('win_fw_step1')}",
                f"    {L.get('win_fw_step2')}",
                f"    {L.get('win_fw_step3')}",
                f"    TCP 52530-52537 ({L.get('parallel_ports')})",
            ])
        elif self.system == "Darwin":
            lines.extend([
                f"▸ {L.get('macos_firewall')}",
                f"    {L.get('macos_fw_step1')}",
                f"    {L.get('macos_fw_step2')}",
            ])

        lines.append("━" * 50)

        return "\n" + "\n".join(lines) + "\n"


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
            on_folder_received=self._on_folder_received,
            on_progress=self._on_receive_progress,
            on_folder_progress=self._on_folder_receive_progress,
            on_status=self._log,
            on_transfer_start=self._on_receive_start
        )
        self.client = TransferClient(
            on_progress=self._on_send_progress,
            on_status=self._log,
            on_complete=self._on_send_complete,
            on_folder_progress=self._on_folder_send_progress
        )

        # 資料夾傳輸狀態
        self.folder_transfer_active = False

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
            f"{L('transfer_port')}: TCP 52526",
            f"{L('parallel_ports')}: TCP 52530-52537"
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

        self.btn_delete_received = ttk.Button(chat_btn_frame, text=L("delete_received"),
                                             command=self._delete_received_files, style='Secondary.TButton')
        self.btn_delete_received.pack(side=tk.LEFT, padx=8)

        self.btn_open_receive = ttk.Button(chat_btn_frame, text=L("open_receive_folder"),
                                          command=self._open_receive_folder, style='Secondary.TButton')
        self.btn_open_receive.pack(side=tk.LEFT)

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
        self.send_file_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.send_folder_btn = ttk.Button(file_select_frame, text=L("send_folder"),
                                         command=self._send_folder, style='Primary.TButton')
        self.send_folder_btn.pack(side=tk.LEFT)

        # 進度條
        progress_frame = ttk.Frame(self.file_labelframe, style='Card.TFrame')
        progress_frame.pack(fill=tk.X, pady=(8, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100,
                                           style='Blue.Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X)

        # 詳細進度資訊 (用於資料夾傳輸)
        self.progress_detail_frame = ttk.Frame(progress_frame, style='Card.TFrame')
        self.progress_detail_frame.pack(fill=tk.X, pady=(4, 0))

        self.progress_label = ttk.Label(self.progress_detail_frame, text="", style='Info.TLabel')
        self.progress_label.pack(side=tk.LEFT, anchor='w')

        # 重置按鈕 (取消後重置進度條)
        self.reset_btn = ttk.Button(self.progress_detail_frame, text=L("reset_progress"),
                                   command=self._reset_progress, style='Secondary.TButton')
        self.reset_btn.pack(side=tk.RIGHT)
        self.reset_btn.pack_forget()  # 預設隱藏

        self.cancel_btn = ttk.Button(self.progress_detail_frame, text=L("cancel_transfer"),
                                    command=self._cancel_transfer, style='Secondary.TButton')
        self.cancel_btn.pack(side=tk.RIGHT, padx=(0, 5))
        self.cancel_btn.pack_forget()  # 預設隱藏

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

        # 版權資訊
        copyright_frame = tk.Frame(right_frame, bg=COLORS["bg_light"])
        copyright_frame.pack(fill=tk.X, pady=(10, 0))

        copyright_text = f"PCPCS v1.0  |  {L('copyright')}  |  {L('website')}"
        copyright_label = tk.Label(
            copyright_frame,
            text=copyright_text,
            font=('Segoe UI', 8),
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_light"],
            cursor="hand2"
        )
        copyright_label.pack(anchor='e')
        copyright_label.bind("<Button-1>", lambda e: self._open_website())

    def _open_website(self):
        """開啟 Perspic 網站"""
        import webbrowser
        webbrowser.open("https://perspic.net")

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

                # 保存選擇的 peer (供重啟後恢復)
                self.lang_mgr.set_last_selected_peer(self.selected_peer_ip, self.selected_peer_name)

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

    def _delete_received_files(self):
        """刪除從選定 peer 收到的所有檔案"""
        if not self.selected_peer_ip:
            messagebox.showwarning(self._t("hint"), self._t("select_chat_target"))
            return

        result = messagebox.askyesno(
            self._t("delete_received_title"),
            self._t("delete_received_msg", name=self.selected_peer_name)
        )

        if result:
            import shutil
            deleted_count = 0

            # 取得所有收到的檔案
            received_files = self.chat_history.get_received_files(self.selected_peer_ip)

            for file_path in received_files:
                try:
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        deleted_count += 1
                    elif os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                except Exception as e:
                    self._log(self._t("delete_fail", msg=str(e)))

            # 清除聊天記錄
            self.chat_history.clear_history(self.selected_peer_ip)
            self.chat_display.config(state='normal')
            self.chat_display.delete('1.0', tk.END)
            self.chat_display.config(state='disabled')

            self._log(self._t("delete_success", count=deleted_count))

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

            def on_progress(step, total, msg):
                def _update():
                    try:
                        if not diag_window.winfo_exists():
                            return
                    except:
                        return
                    # 更新進度顯示
                    progress_pct = int((step / total) * 100)
                    progress_text = f"\n[{progress_pct}%] {msg}"
                    result_text.insert(tk.END, progress_text)
                    result_text.see(tk.END)
                    result_text.update()
                diag_window.after(0, _update)

            def on_complete(results):
                diag_window.after(0, lambda: show_results(results))

            def show_results(results):
                # 檢查視窗是否仍然存在
                try:
                    if not diag_window.winfo_exists():
                        return
                except:
                    return

                result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
                result_text.insert(tk.END, f"{L('diagnostic_result')}\n")
                result_text.insert(tk.END, "=" * 60 + "\n\n")

                sys_info = results.get("system_info", {})
                result_text.insert(tk.END, f"{L('os_label')}: {sys_info.get('os', 'Unknown')} {sys_info.get('os_version', '')[:30]}\n")

                ports = results.get("port_status", {})
                result_text.insert(tk.END, f"\n{L('port_status')}:\n")
                udp_status = L('available') if ports.get('udp_52525') else L('unavailable')
                tcp_status = L('available') if ports.get('tcp_52526') else L('unavailable')

                # UDP 52525 狀態和佔用程式
                udp_note = ""
                if ports.get('udp_52525_note'):
                    udp_note = f" ({ports.get('udp_52525_note')})"
                if ports.get('udp_52525_user'):
                    udp_note = f" ({L('port_used_by', app=ports.get('udp_52525_user'))})"
                result_text.insert(tk.END, f"  UDP 52525: {udp_status}{udp_note}\n")

                # TCP 52526 狀態和佔用程式
                tcp_note = ""
                if ports.get('tcp_52526_note'):
                    tcp_note = f" ({ports.get('tcp_52526_note')})"
                if ports.get('tcp_52526_user'):
                    tcp_note = f" ({L('port_used_by', app=ports.get('tcp_52526_user'))})"
                result_text.insert(tk.END, f"  TCP 52526: {tcp_status}{tcp_note}\n")

                # 並行端口狀態
                parallel_ok = ports.get('parallel_ports_ok', 0)
                parallel_total = ports.get('parallel_ports_total', 8)
                result_text.insert(tk.END, f"\n{L('parallel_ports_status')}:\n")
                result_text.insert(tk.END, f"  TCP 52530-52537: {parallel_ok}/{parallel_total} {L('ports_open')}\n")

                # 顯示被佔用的並行端口
                blocked_ports = [p for p in ports.get('parallel_ports', []) if not p['ok'] and p.get('user')]
                if blocked_ports:
                    for p in blocked_ports:
                        result_text.insert(tk.END, f"    ⚠ Port {p['port']}: {L('port_used_by', app=p['user'])}\n")

                # 防火牆狀態 (含軟體名稱)
                fw = results.get("firewall_status", {})
                fw_software = fw.get('software', '')
                if fw_software:
                    result_text.insert(tk.END, f"\n{L('firewall_software')}: {fw_software}\n")
                result_text.insert(tk.END, f"{L('firewall')}: {fw.get('status', 'unknown')}\n")

                # 如果防火牆開啟且有開放步驟，顯示步驟
                if fw.get('status') == 'enabled' and fw.get('open_steps'):
                    result_text.insert(tk.END, f"\n{L('firewall_open_steps')}\n")
                    for step in fw.get('open_steps', []):
                        result_text.insert(tk.END, f"  {step}\n")

                conn = results.get("connectivity")
                if conn:
                    result_text.insert(tk.END, f"\n{L('connection_test')} ({target}):\n")
                    ping_status = L('success') if conn.get('ping') else L('fail')
                    result_text.insert(tk.END, f"  {L('ping_label')}: {ping_status}")
                    if conn.get('ping_ms'):
                        result_text.insert(tk.END, f" ({conn['ping_ms']:.1f}ms)")
                    tcp_status = L('connected') if conn.get('tcp_52526') else L('not_connected')
                    result_text.insert(tk.END, f"\n  TCP 52526: {tcp_status}\n")

                    # 並行端口連接測試結果
                    parallel_conn_ok = conn.get('parallel_ports_ok', 0)
                    parallel_conn_total = conn.get('parallel_ports_total', 8)
                    result_text.insert(tk.END, f"\n{L('parallel_ports_test')}:\n")
                    result_text.insert(tk.END, f"  TCP 52530-52537: {parallel_conn_ok}/{parallel_conn_total} {L('connected')}\n")
                    if parallel_conn_ok < parallel_conn_total:
                        failed_ports = [p['port'] for p in conn.get('parallel_ports_detail', []) if not p['ok']]
                        if failed_ports:
                            result_text.insert(tk.END, f"  {L('not_connected')}: {', '.join(map(str, failed_ports))}\n")

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
                target=lambda: self.diagnostic.run_full_diagnostic(target, on_complete, on_progress),
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
        self.send_folder_btn.config(state='disabled')
        self.cancel_btn.pack(side=tk.RIGHT, padx=(0, 5))  # 顯示取消按鈕
        self.reset_btn.pack_forget()  # 隱藏重置按鈕
        self.progress_var.set(0)
        self.client.send_file(self.selected_peer_ip, filepath)

    def _browse_folder(self):
        """選擇要發送的資料夾"""
        folder_path = filedialog.askdirectory(title=self._t("select_folder_title"))
        if folder_path:
            self.file_path_var.set(folder_path)

    def _send_folder(self):
        """發送資料夾"""
        if not self.selected_peer_ip:
            messagebox.showwarning(self._t("hint"), self._t("select_target_first"))
            return

        # 先讓使用者選擇資料夾
        folder_path = filedialog.askdirectory(title=self._t("select_folder_title"))
        if not folder_path:
            return

        if not os.path.isdir(folder_path):
            messagebox.showwarning(self._t("hint"), self._t("select_valid_folder"))
            return

        # 計算資料夾總大小
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))
                file_count += 1

        if file_count == 0:
            messagebox.showwarning(self._t("hint"), self._t("folder_empty"))
            return

        self.transfer_size = total_size
        self.transfer_start_time = time.time()
        self.folder_transfer_active = True

        self._log(self._t("sending_folder"))
        self.send_file_btn.config(state='disabled')
        self.send_folder_btn.config(state='disabled')
        self.cancel_btn.pack(side=tk.RIGHT, padx=(0, 5))  # 顯示取消按鈕
        self.reset_btn.pack_forget()  # 隱藏重置按鈕
        self.progress_var.set(0)

        # 保存資料夾路徑供完成時使用
        self._current_folder_path = folder_path
        self._current_folder_files = file_count

        self.client.send_folder(self.selected_peer_ip, folder_path)

    def _cancel_transfer(self):
        """取消傳輸 (檔案或資料夾)"""
        self.client.cancel_folder_transfer()  # 這個方法也會取消並行傳輸
        self._log(self._t("transfer_cancelled"))
        # 顯示重置按鈕
        self.cancel_btn.pack_forget()
        self.reset_btn.pack(side=tk.RIGHT)

    def _reset_progress(self):
        """重置進度條"""
        self.progress_var.set(0)
        self.progress_label.config(text="")
        self.reset_btn.pack_forget()
        self.send_file_btn.config(state='normal')
        self.send_folder_btn.config(state='normal')
        self.folder_transfer_active = False
        self.transfer_start_time = None
        self.transfer_size = 0

    def _on_folder_send_progress(self, current: int, total: int, filename: str, file_progress: float, overall_progress: float, status: str):
        """資料夾發送進度回調"""
        self.root.after(0, lambda: self._update_folder_progress(current, total, filename, file_progress, overall_progress, status, "send"))

    def _on_receive_start(self, total_size: int):
        """接收開始回調 - 用於 ETA 計算"""
        def _start():
            self.transfer_size = total_size
            self.transfer_start_time = time.time()
            self._log(self._t("transfer_warning"))
        self.root.after(0, _start)

    def _on_folder_receive_progress(self, current: int, total: int, filename: str, file_progress: float, overall_progress: float, status: str):
        """資料夾接收進度回調"""
        self.root.after(0, lambda: self._update_folder_progress(current, total, filename, file_progress, overall_progress, status, "receive"))

    def _update_folder_progress(self, current: int, total: int, filename: str, file_progress: float, overall_progress: float, status: str, direction: str):
        """更新資料夾傳輸進度顯示"""
        self.progress_var.set(overall_progress)

        # 狀態圖示
        status_icon = ""
        if status == "completed":
            status_icon = "✓ "
        elif status == "skipped":
            status_icon = "⊘ "
        elif status == "sending" or status == "receiving":
            status_icon = "↑ " if direction == "send" else "↓ "

        # 計算速度和 ETA
        speed_str = ""
        eta_str = ""
        if self.transfer_start_time and self.transfer_size > 0:
            elapsed = time.time() - self.transfer_start_time
            if elapsed > 0 and overall_progress > 0:
                speed = (overall_progress / 100 * self.transfer_size) / elapsed
                speed_str = f" | {self._format_size(speed)}/s"

                # 計算 ETA
                remaining_bytes = self.transfer_size * (1 - overall_progress / 100)
                if speed > 0:
                    eta_seconds = remaining_bytes / speed
                    eta_str = f" | {self._t('eta_label')}: {self._format_time(eta_seconds)}"

        # 顯示格式：(3/10) filename.txt [78%]
        progress_text = f"{status_icon}({current}/{total}) {filename}"
        if status in ["sending", "receiving"]:
            progress_text += f" [{file_progress:.0f}%]"
        progress_text += f" - {overall_progress:.1f}%{speed_str}{eta_str}"

        self.progress_label.config(text=progress_text)

    def _on_send_progress(self, progress: float, message: str):
        self.root.after(0, lambda: self._update_progress(progress, message))

    def _on_receive_progress(self, progress: float, message: str):
        self.root.after(0, lambda: self._update_progress(progress, message))

    def _update_progress(self, progress: float, message: str):
        self.progress_var.set(progress)

        speed_str = ""
        eta_str = ""
        if self.transfer_start_time and self.transfer_size > 0:
            elapsed = time.time() - self.transfer_start_time
            if elapsed > 0 and progress > 0:
                speed = (progress / 100 * self.transfer_size) / elapsed
                speed_str = f" | {self._format_size(speed)}/s"

                # 計算 ETA
                remaining_bytes = self.transfer_size * (1 - progress / 100)
                if speed > 0:
                    eta_seconds = remaining_bytes / speed
                    eta_str = f" | {self._t('eta_label')}: {self._format_time(eta_seconds)}"

        self.progress_label.config(text=f"{message} ({progress:.1f}%){speed_str}{eta_str}")

    def _on_send_complete(self, success: bool, message: str):
        self.root.after(0, lambda: self._handle_send_complete(success, message))

    def _handle_send_complete(self, success: bool, message: str):
        self.send_btn.config(state='normal')
        self.send_file_btn.config(state='normal')
        self.send_folder_btn.config(state='normal')
        self.cancel_btn.pack_forget()  # 隱藏取消按鈕
        self.reset_btn.pack_forget()   # 隱藏重置按鈕
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

            # 資料夾傳輸完成
            if self.folder_transfer_active:
                folder_name = os.path.basename(getattr(self, '_current_folder_path', ''))
                file_count = getattr(self, '_current_folder_files', 0)
                self._add_chat_message(
                    get_hostname(),
                    f"📁 {folder_name} ({file_count} files)",
                    is_file=True,
                    file_info={"size": self.transfer_size, "speed": speed_str}
                )
                self.folder_transfer_active = False
            elif "檔案" in message or "file" in message.lower():
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
            self.folder_transfer_active = False

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

    def _on_folder_received(self, sender_ip: str, sender_name: str, folder_path: str, total_files: int, total_size: int, sender_platform: str = "Unknown"):
        """資料夾接收完成回調"""
        self.root.after(0, lambda: self._handle_folder_received(sender_ip, sender_name, folder_path, total_files, total_size, sender_platform))

    def _handle_folder_received(self, sender_ip: str, sender_name: str, folder_path: str, total_files: int, total_size: int, sender_platform: str = "Unknown"):
        """處理資料夾接收完成"""
        self._ensure_peer_exists(sender_ip, sender_name, sender_platform)

        folder_name = os.path.basename(folder_path)
        size_str = self._format_size(total_size)

        file_info = {"size": total_size, "path": folder_path, "file_count": total_files}

        if self.selected_peer_ip == sender_ip:
            self._add_chat_message(sender_name, f"📁 {folder_name} ({total_files} files)", is_file=True, file_info=file_info)
        else:
            self.chat_history.save_message(sender_ip, sender_name, f"📁 {folder_name} ({total_files} files)", is_file=True, file_info=file_info)

        self._log(self._t("received_folder", name=folder_name, count=total_files))

        # 重設進度條
        self.progress_var.set(0)
        self.progress_label.config(text="")

        result = messagebox.askyesno(
            self._t("folder_received_title", name=sender_name),
            self._t("folder_received_msg", foldername=folder_name, count=total_files, size=size_str)
        )
        if result:
            self._open_folder(folder_path)

    def _open_folder(self, folder_path: str):
        """開啟指定資料夾"""
        import platform
        import subprocess

        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", folder_path])
        else:
            subprocess.run(["xdg-open", folder_path])

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

    def _format_time(self, seconds: float) -> str:
        """格式化時間為人類可讀格式"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"

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

        # 恢復上次選擇的 peer
        self.root.after(1000, self._restore_last_peer)

        self.root.mainloop()

    def _restore_last_peer(self):
        """恢復上次選擇的 peer 並載入聊天記錄"""
        last_ip, last_name = self.lang_mgr.get_last_selected_peer()
        if last_ip and last_name:
            self.selected_peer_ip = last_ip
            self.selected_peer_name = last_name
            self.target_label.config(text=f"{self.selected_peer_name} ({self.selected_peer_ip})")
            self._load_chat_history()
            self._log(self._t("selected", name=self.selected_peer_name))


def main():
    app = PCPCSApp()
    app.run()


if __name__ == "__main__":
    main()
