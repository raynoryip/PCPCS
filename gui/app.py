"""
PCPCS GUI 介面
使用 Tkinter 實作跨平台圖形介面
Modern UI with Perspic Blue Theme
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

# Perspic 藍色主題色
COLORS = {
    "primary": "#0088FF",          # 主藍色
    "primary_dark": "#0066CC",     # 深藍色
    "primary_light": "#00B4FF",    # 淺藍色
    "accent": "#00D4FF",           # 強調色
    "bg_dark": "#1a1a2e",          # 深色背景
    "bg_medium": "#16213e",        # 中等背景
    "bg_light": "#0f3460",         # 淺色背景
    "text_primary": "#ffffff",     # 主要文字
    "text_secondary": "#a0a0a0",   # 次要文字
    "success": "#00c853",          # 成功綠
    "warning": "#ffab00",          # 警告黃
    "error": "#ff5252",            # 錯誤紅
    "card_bg": "#1e2a4a",          # 卡片背景
    "border": "#2a3f5f",           # 邊框色
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

        # 移除已存在的相同 IP
        connections = [c for c in connections if c.get("ip") != ip]

        # 添加到最前面
        connections.insert(0, {
            "ip": ip,
            "hostname": hostname,
            "platform": platform,
            "last_connected": datetime.datetime.now().isoformat()
        })

        # 只保留最近 20 個
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
            "network_type": self._check_network_type(),
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
        import socket
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
        import subprocess
        results = {
            "udp_52525": False,
            "tcp_52526": False,
            "udp_52525_in_use": False,
            "tcp_52526_in_use": False,
            "udp_52525_process": None,
            "tcp_52526_process": None
        }

        # 檢查 UDP 52525
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 52525))
            sock.close()
            results["udp_52525"] = True
        except OSError as e:
            err_str = str(e)
            if "Address already in use" in err_str or "Only one usage" in err_str or "10048" in err_str:
                results["udp_52525"] = True
                results["udp_52525_in_use"] = True
                results["udp_52525_process"] = self._get_process_using_port(52525, "udp")

        # 檢查 TCP 52526
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 52526))
            sock.close()
            results["tcp_52526"] = True
        except OSError as e:
            err_str = str(e)
            if "Address already in use" in err_str or "Only one usage" in err_str or "10048" in err_str:
                results["tcp_52526"] = True
                results["tcp_52526_in_use"] = True
                results["tcp_52526_process"] = self._get_process_using_port(52526, "tcp")

        return results

    def _get_process_using_port(self, port: int, protocol: str) -> str:
        """取得使用特定端口的進程名稱"""
        import subprocess
        try:
            if self.system == "Windows":
                proto_filter = "UDP" if protocol == "udp" else "TCP"
                proc = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True, text=True, timeout=10
                )
                for line in proc.stdout.split('\n'):
                    if f":{port}" in line and proto_filter in line.upper():
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            task_proc = subprocess.run(
                                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                                capture_output=True, text=True, timeout=5
                            )
                            if task_proc.stdout.strip():
                                process_name = task_proc.stdout.strip().split(',')[0].strip('"')
                                return f"{process_name} (PID: {pid})"
                return None
            else:
                try:
                    proto_flag = "-u" if protocol == "udp" else "-t"
                    proc = subprocess.run(
                        ["ss", proto_flag, "-lpn", f"sport = :{port}"],
                        capture_output=True, text=True, timeout=5
                    )
                    if proc.returncode == 0 and proc.stdout:
                        import re
                        match = re.search(r'users:\(\("([^"]+)",pid=(\d+)', proc.stdout)
                        if match:
                            return f"{match.group(1)} (PID: {match.group(2)})"
                except:
                    pass

                try:
                    proto_flag = "UDP" if protocol == "udp" else "TCP"
                    proc = subprocess.run(
                        ["lsof", "-i", f"{proto_flag}:{port}"],
                        capture_output=True, text=True, timeout=5
                    )
                    if proc.returncode == 0 and proc.stdout:
                        lines = proc.stdout.strip().split('\n')
                        if len(lines) > 1:
                            parts = lines[1].split()
                            if len(parts) >= 2:
                                return f"{parts[0]} (PID: {parts[1]})"
                except:
                    pass

                return None
        except Exception as e:
            return None

    def _check_network_type(self) -> dict:
        """檢測網路類型 (公共/私人)"""
        import subprocess
        result = {
            "is_public": False,
            "network_name": "Unknown",
            "warning": None
        }

        try:
            if self.system == "Windows":
                proc = subprocess.run(
                    ["powershell", "-Command",
                     "Get-NetConnectionProfile | Select-Object Name, NetworkCategory | ConvertTo-Json"],
                    capture_output=True, text=True, timeout=10
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    try:
                        profiles = json.loads(proc.stdout)
                        if isinstance(profiles, dict):
                            profiles = [profiles]
                        for profile in profiles:
                            name = profile.get("Name", "Unknown")
                            category = profile.get("NetworkCategory", 0)
                            if category == 0:
                                result["is_public"] = True
                                result["network_name"] = name
                                result["warning"] = f"警告: 目前連接到公共網路 '{name}'！\n不建議在公共網路上使用 PCPCS。"
                                break
                            else:
                                result["network_name"] = name
                    except json.JSONDecodeError:
                        pass

            elif self.system == "Linux":
                try:
                    proc = subprocess.run(
                        ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"],
                        capture_output=True, text=True, timeout=5
                    )
                    if proc.returncode == 0:
                        for line in proc.stdout.strip().split('\n'):
                            if line:
                                parts = line.split(':')
                                if len(parts) >= 2:
                                    result["network_name"] = parts[0]
                                    conn_type = parts[1].lower()
                                    if "wifi" in conn_type or "wireless" in conn_type:
                                        wifi_proc = subprocess.run(
                                            ["nmcli", "-t", "-f", "SECURITY", "device", "wifi", "list"],
                                            capture_output=True, text=True, timeout=5
                                        )
                                        if wifi_proc.returncode == 0:
                                            for wifi_line in wifi_proc.stdout.split('\n'):
                                                if not wifi_line.strip() or wifi_line.strip() == "--":
                                                    result["is_public"] = True
                                                    result["warning"] = "警告: 可能連接到開放的 WiFi 網路！"
                                                    break
                except:
                    pass

                local_ip = self.local_ip
                if not (local_ip.startswith("10.") or local_ip.startswith("172.") or local_ip.startswith("192.168.")):
                    result["is_public"] = True
                    result["warning"] = "警告: IP 地址不在私有範圍內，可能是公共網路！"

        except Exception as e:
            result["error"] = str(e)

        return result

    def _detect_security_software(self) -> dict:
        """檢測安裝的安全軟件/防火牆"""
        import subprocess
        result = {
            "detected": [],
            "firewall_provider": "Unknown"
        }

        security_software = {
            "bdagent.exe": "Bitdefender",
            "bdservicehost.exe": "Bitdefender",
            "vsserv.exe": "Bitdefender",
            "norton.exe": "Norton",
            "ns.exe": "Norton",
            "mcshield.exe": "McAfee",
            "mcafee": "McAfee",
            "avp.exe": "Kaspersky",
            "kavtray.exe": "Kaspersky",
            "ekrn.exe": "ESET",
            "egui.exe": "ESET",
            "avastui.exe": "Avast",
            "avastsvc.exe": "Avast",
            "avgui.exe": "AVG",
            "avgsvc.exe": "AVG",
            "cmdagent.exe": "Comodo",
            "cis.exe": "Comodo",
            "zonealarm.exe": "ZoneAlarm",
            "vsmon.exe": "ZoneAlarm",
            "mbam.exe": "Malwarebytes",
            "mbamservice.exe": "Malwarebytes",
            "sophosui.exe": "Sophos",
            "savservice.exe": "Sophos",
            "panda": "Panda",
            "psanhost.exe": "Panda",
            "f-secure": "F-Secure",
            "fsgk32.exe": "F-Secure",
            "dwengine.exe": "Dr.Web",
            "spidergate.exe": "Dr.Web",
            "360tray.exe": "360 Security",
            "360sd.exe": "360 Security",
        }

        try:
            if self.system == "Windows":
                try:
                    proc = subprocess.run(
                        ["wmic", "/namespace:\\\\root\\SecurityCenter2", "path",
                         "AntiVirusProduct", "get", "displayName"],
                        capture_output=True, text=True, timeout=10
                    )
                    if proc.returncode == 0:
                        lines = proc.stdout.strip().split('\n')
                        for line in lines[1:]:
                            name = line.strip()
                            if name and name != "displayName":
                                result["detected"].append(name)
                                if result["firewall_provider"] == "Unknown":
                                    result["firewall_provider"] = name
                except:
                    pass

                try:
                    proc = subprocess.run(
                        ["wmic", "/namespace:\\\\root\\SecurityCenter2", "path",
                         "FirewallProduct", "get", "displayName"],
                        capture_output=True, text=True, timeout=10
                    )
                    if proc.returncode == 0:
                        lines = proc.stdout.strip().split('\n')
                        for line in lines[1:]:
                            name = line.strip()
                            if name and name != "displayName" and name not in result["detected"]:
                                result["detected"].append(name)
                except:
                    pass

                if not result["detected"]:
                    try:
                        proc = subprocess.run(
                            ["tasklist", "/fo", "csv"],
                            capture_output=True, text=True, timeout=10
                        )
                        processes = proc.stdout.lower()
                        detected_names = set()
                        for proc_name, display_name in security_software.items():
                            if proc_name.lower() in processes:
                                detected_names.add(display_name)
                        result["detected"] = list(detected_names)
                        if result["detected"]:
                            result["firewall_provider"] = result["detected"][0]
                    except:
                        pass

            elif self.system == "Linux":
                try:
                    proc = subprocess.run(["which", "ufw"], capture_output=True, timeout=5)
                    if proc.returncode == 0:
                        result["detected"].append("UFW (Uncomplicated Firewall)")
                        result["firewall_provider"] = "UFW"
                except:
                    pass

                try:
                    proc = subprocess.run(["which", "firewalld"], capture_output=True, timeout=5)
                    if proc.returncode == 0:
                        result["detected"].append("firewalld")
                        if result["firewall_provider"] == "Unknown":
                            result["firewall_provider"] = "firewalld"
                except:
                    pass

                try:
                    proc = subprocess.run(["which", "clamscan"], capture_output=True, timeout=5)
                    if proc.returncode == 0:
                        result["detected"].append("ClamAV")
                except:
                    pass

        except Exception as e:
            result["error"] = str(e)

        if not result["detected"]:
            if self.system == "Windows":
                result["detected"].append("Windows Defender")
                result["firewall_provider"] = "Windows Defender"
            elif self.system == "Linux":
                result["detected"].append("iptables (系統內建)")
                result["firewall_provider"] = "iptables"

        return result

    def _check_firewall(self) -> dict:
        """檢查防火牆狀態"""
        import subprocess
        result = {
            "status": "unknown",
            "details": "",
            "pcpcs_allowed": "unknown",
            "software": self._detect_security_software()
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
        """根據診斷結果生成建議"""
        recommendations = []

        network_type = results.get("network_type", {})
        if network_type.get("is_public"):
            recommendations.append({
                "issue": "公共網路警告",
                "solution": "您目前連接到公共網路，存在安全風險！",
                "commands": [
                    "建議:",
                    "1. 避免在公共 WiFi (咖啡廳、機場等) 使用 PCPCS",
                    "2. 如必須使用，請確保防火牆設定嚴格限制",
                    "3. 只允許已知 IP 地址的連線",
                    "4. 傳輸敏感檔案時請使用加密"
                ]
            })

        fw = results.get("firewall_status", {})
        software = fw.get("software", {})
        provider = software.get("firewall_provider", "Unknown")
        detected = software.get("detected", [])

        if self.system == "Windows":
            third_party_guides = {
                "Bitdefender": {
                    "issue": f"檢測到 Bitdefender 防火牆",
                    "solution": "在 Bitdefender 中設定 PCPCS 規則:",
                    "commands": [
                        "1. 開啟 Bitdefender → Protection → Firewall",
                        "2. 點擊 Settings → Rules → Add Rule",
                        "3. 新增規則允許 python.exe (或 pythonw.exe):",
                        "   - Permission: Allow",
                        "   - Network Type: Any",
                        "   - Protocol: TCP + UDP",
                        "   - Direction: Both (Inbound + Outbound)",
                        "   - Local Port: 52525, 52526",
                        "   - Remote Address: 不要限制 (留空或 Any)"
                    ]
                },
                "Norton": {
                    "issue": f"檢測到 Norton 防火牆",
                    "solution": "在 Norton 中允許 PCPCS:",
                    "commands": [
                        "1. 開啟 Norton → Settings → Firewall",
                        "2. 點擊 Program Control → Add",
                        "3. 找到 python.exe 並設為 Allow",
                        "4. 或在 Traffic Rules 中添加端口 52525/UDP 和 52526/TCP"
                    ]
                },
                "Windows Defender": {
                    "issue": "使用 Windows Defender 防火牆",
                    "solution": "在 Windows Defender 中開放端口 (以管理員身份執行):",
                    "commands": [
                        'netsh advfirewall firewall add rule name="PCPCS UDP" dir=in action=allow protocol=UDP localport=52525',
                        'netsh advfirewall firewall add rule name="PCPCS TCP" dir=in action=allow protocol=TCP localport=52526'
                    ]
                }
            }

            for sw in detected:
                for key, guide in third_party_guides.items():
                    if key.lower() in sw.lower():
                        recommendations.append(guide)
                        break

            if not recommendations or (len(recommendations) == 1 and network_type.get("is_public")):
                recommendations.append(third_party_guides.get("Windows Defender"))

        elif self.system == "Linux":
            if fw.get("pcpcs_allowed") == "no":
                recommendations.append({
                    "issue": "Linux UFW 防火牆未開放 PCPCS 端口",
                    "solution": "執行以下命令開放端口:",
                    "commands": [
                        "sudo ufw allow 52525/udp comment 'PCPCS Discovery'",
                        "sudo ufw allow 52526/tcp comment 'PCPCS Transfer'",
                        "sudo ufw reload"
                    ]
                })

        conn = results.get("connectivity", {})
        if conn:
            if not conn.get("ping"):
                recommendations.append({
                    "issue": "無法 Ping 到目標電腦",
                    "solution": "確認兩台電腦在同一個網段，並檢查目標電腦的防火牆是否允許 ICMP",
                    "commands": [
                        f"本機 IP: {self.local_ip}",
                        "確認目標 IP 在同一網段 (如 192.168.1.x)"
                    ]
                })
            elif conn.get("ping") and not conn.get("tcp_52526"):
                recommendations.append({
                    "issue": "Ping 成功但 TCP 52526 連接失敗",
                    "solution": f"目標電腦的 {provider} 防火牆可能阻擋了 TCP 52526 端口",
                    "commands": [
                        "請在目標電腦上:",
                        "1. 確認 PCPCS 正在運行",
                        "2. 檢查防火牆是否允許 TCP 52526 入站連線"
                    ]
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
╚══════════════════════════════════════════════════════════════╝
"""
        return guide


class PCPCSApp:
    """PCPCS 主應用程式 - Modern UI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"PCPCS - {get_hostname()}")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 650)

        # 設定深色背景
        self.root.configure(bg=COLORS["bg_dark"])

        # 設定樣式
        self.style = ttk.Style()
        self._setup_styles()

        # 載入 Logo
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

        # 傳輸速度追蹤
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
                # 縮小 logo
                img = img.resize((180, 135), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"無法載入 Logo: {e}")
            self.logo_image = None

    def _setup_styles(self):
        """設定 Modern UI 樣式"""
        self.style.theme_use('clam')

        # 主框架樣式
        self.style.configure('Dark.TFrame', background=COLORS["bg_dark"])
        self.style.configure('Card.TFrame', background=COLORS["card_bg"])

        # 標籤樣式
        self.style.configure('Title.TLabel',
                           background=COLORS["bg_dark"],
                           foreground=COLORS["text_primary"],
                           font=('Segoe UI', 14, 'bold'))
        self.style.configure('Subtitle.TLabel',
                           background=COLORS["bg_dark"],
                           foreground=COLORS["text_secondary"],
                           font=('Segoe UI', 10))
        self.style.configure('Card.TLabel',
                           background=COLORS["card_bg"],
                           foreground=COLORS["text_primary"],
                           font=('Segoe UI', 10))
        self.style.configure('CardTitle.TLabel',
                           background=COLORS["card_bg"],
                           foreground=COLORS["primary_light"],
                           font=('Segoe UI', 11, 'bold'))
        self.style.configure('Info.TLabel',
                           background=COLORS["card_bg"],
                           foreground=COLORS["text_secondary"],
                           font=('Consolas', 9))

        # 按鈕樣式
        self.style.configure('Accent.TButton',
                           background=COLORS["primary"],
                           foreground=COLORS["text_primary"],
                           font=('Segoe UI', 10),
                           padding=(15, 8))
        self.style.map('Accent.TButton',
                      background=[('active', COLORS["primary_light"]), ('pressed', COLORS["primary_dark"])])

        self.style.configure('Secondary.TButton',
                           background=COLORS["bg_light"],
                           foreground=COLORS["text_primary"],
                           font=('Segoe UI', 9),
                           padding=(10, 5))
        self.style.map('Secondary.TButton',
                      background=[('active', COLORS["border"])])

        # LabelFrame 樣式
        self.style.configure('Card.TLabelframe',
                           background=COLORS["card_bg"],
                           foreground=COLORS["primary_light"],
                           font=('Segoe UI', 10, 'bold'))
        self.style.configure('Card.TLabelframe.Label',
                           background=COLORS["card_bg"],
                           foreground=COLORS["primary_light"],
                           font=('Segoe UI', 10, 'bold'))

        # Entry 樣式
        self.style.configure('Modern.TEntry',
                           fieldbackground=COLORS["bg_medium"],
                           foreground=COLORS["text_primary"],
                           insertcolor=COLORS["text_primary"],
                           font=('Consolas', 11))

        # Progressbar 樣式
        self.style.configure('Blue.Horizontal.TProgressbar',
                           background=COLORS["primary"],
                           troughcolor=COLORS["bg_medium"])

    def _create_ui(self):
        """建立 Modern 使用者介面"""
        # 主框架
        main_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 左側 - Logo、節點列表和最近連線
        left_frame = tk.Frame(main_frame, bg=COLORS["bg_dark"], width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_frame.pack_propagate(False)

        # Logo 區域
        if self.logo_image:
            logo_label = tk.Label(left_frame, image=self.logo_image, bg=COLORS["bg_dark"])
            logo_label.pack(pady=(0, 10))

        # 本機資訊卡片
        info_card = tk.Frame(left_frame, bg=COLORS["card_bg"], relief='flat', bd=0)
        info_card.pack(fill=tk.X, pady=(0, 10))

        # 內部 padding
        info_inner = tk.Frame(info_card, bg=COLORS["card_bg"])
        info_inner.pack(fill=tk.X, padx=12, pady=10)

        tk.Label(info_inner, text="本機資訊", bg=COLORS["card_bg"],
                fg=COLORS["primary_light"], font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        tk.Label(info_inner, text=f"名稱: {get_hostname()}", bg=COLORS["card_bg"],
                fg=COLORS["text_secondary"], font=('Consolas', 9)).pack(anchor='w', pady=(5, 0))
        tk.Label(info_inner, text=f"IP: {get_local_ip()}", bg=COLORS["card_bg"],
                fg=COLORS["text_secondary"], font=('Consolas', 9)).pack(anchor='w')
        tk.Label(info_inner, text="UDP: 52525 | TCP: 52526", bg=COLORS["card_bg"],
                fg=COLORS["text_secondary"], font=('Consolas', 9)).pack(anchor='w')

        # 已發現的電腦卡片
        peer_card = tk.Frame(left_frame, bg=COLORS["card_bg"], relief='flat', bd=0)
        peer_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        peer_inner = tk.Frame(peer_card, bg=COLORS["card_bg"])
        peer_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        tk.Label(peer_inner, text="已發現的電腦", bg=COLORS["card_bg"],
                fg=COLORS["primary_light"], font=('Segoe UI', 11, 'bold')).pack(anchor='w')

        # 節點列表
        self.peer_listbox = tk.Listbox(
            peer_inner,
            font=('Consolas', 10),
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            selectbackground=COLORS["primary"],
            selectforeground=COLORS["text_primary"],
            highlightthickness=0,
            bd=0,
            relief='flat'
        )
        self.peer_listbox.pack(fill=tk.BOTH, expand=True, pady=(8, 8))
        self.peer_listbox.bind('<<ListboxSelect>>', self._on_peer_select)

        # 按鈕區
        btn_frame = tk.Frame(peer_inner, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="重新掃描", command=self._refresh_peers,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="手動添加", command=self._manual_add_ip,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="診斷", command=self._show_diagnostic,
                  style='Secondary.TButton').pack(side=tk.LEFT)

        # 最近連線卡片
        recent_card = tk.Frame(left_frame, bg=COLORS["card_bg"], relief='flat', bd=0)
        recent_card.pack(fill=tk.X)

        recent_inner = tk.Frame(recent_card, bg=COLORS["card_bg"])
        recent_inner.pack(fill=tk.X, padx=12, pady=10)

        recent_header = tk.Frame(recent_inner, bg=COLORS["card_bg"])
        recent_header.pack(fill=tk.X)

        tk.Label(recent_header, text="最近連線", bg=COLORS["card_bg"],
                fg=COLORS["primary_light"], font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)

        # 最近連線列表
        self.recent_listbox = tk.Listbox(
            recent_inner,
            font=('Consolas', 9),
            bg=COLORS["bg_medium"],
            fg=COLORS["text_secondary"],
            selectbackground=COLORS["primary"],
            selectforeground=COLORS["text_primary"],
            highlightthickness=0,
            bd=0,
            relief='flat',
            height=4
        )
        self.recent_listbox.pack(fill=tk.X, pady=(8, 0))
        self.recent_listbox.bind('<<ListboxSelect>>', self._on_recent_select)
        self.recent_listbox.bind('<Double-Button-1>', self._connect_recent)

        # 載入最近連線
        self._load_recent_connections()

        # 右側 - 聊天和傳輸區
        right_frame = tk.Frame(main_frame, bg=COLORS["bg_dark"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 對話對象顯示
        target_frame = tk.Frame(right_frame, bg=COLORS["bg_dark"])
        target_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(target_frame, text="對話對象:", bg=COLORS["bg_dark"],
                fg=COLORS["text_secondary"], font=('Segoe UI', 11)).pack(side=tk.LEFT)
        self.target_label = tk.Label(target_frame, text="(請從左側選擇電腦)",
                                    bg=COLORS["bg_dark"], fg=COLORS["primary_light"],
                                    font=('Segoe UI', 12, 'bold'))
        self.target_label.pack(side=tk.LEFT, padx=(10, 0))

        # 聊天對話卡片
        chat_card = tk.Frame(right_frame, bg=COLORS["card_bg"], relief='flat', bd=0)
        chat_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        chat_inner = tk.Frame(chat_card, bg=COLORS["card_bg"])
        chat_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        chat_header = tk.Frame(chat_inner, bg=COLORS["card_bg"])
        chat_header.pack(fill=tk.X)

        tk.Label(chat_header, text="對話", bg=COLORS["card_bg"],
                fg=COLORS["primary_light"], font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)

        ttk.Button(chat_header, text="清除記錄", command=self._clear_chat_history,
                  style='Secondary.TButton').pack(side=tk.RIGHT)

        # 聊天記錄顯示區
        self.chat_display = scrolledtext.ScrolledText(
            chat_inner,
            font=('Consolas', 10),
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            state='disabled',
            wrap=tk.WORD,
            relief='flat',
            bd=0
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(8, 8))

        # 設定聊天顯示的標籤樣式
        self.chat_display.tag_configure('self', foreground=COLORS["success"], font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('peer', foreground=COLORS["primary_light"], font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('system', foreground=COLORS["text_secondary"], font=('Consolas', 9, 'italic'))
        self.chat_display.tag_configure('file', foreground=COLORS["accent"], font=('Consolas', 10))
        self.chat_display.tag_configure('timestamp', foreground=COLORS["text_secondary"], font=('Consolas', 8))

        # 輸入區
        input_frame = tk.Frame(chat_inner, bg=COLORS["card_bg"])
        input_frame.pack(fill=tk.X)

        self.message_input = tk.Entry(
            input_frame,
            font=('Consolas', 11),
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief='flat',
            bd=0
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
        self.message_input.bind('<Return>', lambda e: self._send_text())

        self.send_btn = ttk.Button(input_frame, text="發送", command=self._send_text,
                                   style='Accent.TButton')
        self.send_btn.pack(side=tk.LEFT)

        # 檔案傳輸卡片
        file_card = tk.Frame(right_frame, bg=COLORS["card_bg"], relief='flat', bd=0)
        file_card.pack(fill=tk.X, pady=(0, 10))

        file_inner = tk.Frame(file_card, bg=COLORS["card_bg"])
        file_inner.pack(fill=tk.X, padx=12, pady=10)

        tk.Label(file_inner, text="檔案傳輸", bg=COLORS["card_bg"],
                fg=COLORS["primary_light"], font=('Segoe UI', 11, 'bold')).pack(anchor='w')

        file_select_frame = tk.Frame(file_inner, bg=COLORS["card_bg"])
        file_select_frame.pack(fill=tk.X, pady=(8, 0))

        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(
            file_select_frame,
            textvariable=self.file_path_var,
            font=('Consolas', 10),
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief='flat',
            bd=0
        )
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=6)

        ttk.Button(file_select_frame, text="選擇", command=self._browse_file,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 5))
        self.send_file_btn = ttk.Button(file_select_frame, text="發送檔案",
                                        command=self._send_file, style='Accent.TButton')
        self.send_file_btn.pack(side=tk.LEFT)

        # 進度條
        progress_frame = tk.Frame(file_inner, bg=COLORS["card_bg"])
        progress_frame.pack(fill=tk.X, pady=(8, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, style='Blue.Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = tk.Label(progress_frame, text="", bg=COLORS["card_bg"],
                                       fg=COLORS["text_secondary"], font=('Consolas', 9))
        self.progress_label.pack(anchor='w', pady=(4, 0))

        # 系統日誌
        log_card = tk.Frame(right_frame, bg=COLORS["card_bg"], relief='flat', bd=0)
        log_card.pack(fill=tk.X)

        log_inner = tk.Frame(log_card, bg=COLORS["card_bg"])
        log_inner.pack(fill=tk.X, padx=12, pady=10)

        tk.Label(log_inner, text="系統日誌", bg=COLORS["card_bg"],
                fg=COLORS["primary_light"], font=('Segoe UI', 11, 'bold')).pack(anchor='w')

        self.log_text = scrolledtext.ScrolledText(
            log_inner,
            height=4,
            font=('Consolas', 9),
            bg=COLORS["bg_medium"],
            fg=COLORS["text_secondary"],
            state='disabled',
            relief='flat',
            bd=0
        )
        self.log_text.pack(fill=tk.X, pady=(8, 0))

    def _load_recent_connections(self):
        """載入最近連線到列表"""
        self.recent_listbox.delete(0, tk.END)
        connections = self.recent_connections.load()

        for conn in connections:
            ip = conn.get("ip", "")
            hostname = conn.get("hostname", "Unknown")
            platform = conn.get("platform", "")
            os_icon = "L" if "Linux" in platform else "W" if "Windows" in platform else "?"
            display = f"[{os_icon}] {hostname} ({ip})"
            self.recent_listbox.insert(tk.END, display)

    def _on_recent_select(self, event):
        """選擇最近連線"""
        pass  # 單擊只是選中，雙擊才連接

    def _connect_recent(self, event):
        """雙擊連接最近連線"""
        selection = self.recent_listbox.curselection()
        if selection:
            connections = self.recent_connections.load()
            if selection[0] < len(connections):
                conn = connections[selection[0]]
                ip = conn.get("ip", "")
                hostname = conn.get("hostname", "")
                platform = conn.get("platform", "Unknown")

                # 添加到節點列表並選中
                self._add_and_select_peer(ip, hostname, platform)

    def _add_and_select_peer(self, ip: str, hostname: str, platform: str):
        """添加節點並選中"""
        if ip not in self.discovery.peers:
            peer = PeerInfo(ip, hostname, platform)
            peer.is_reachable = True
            self.discovery.peers[ip] = peer
            self._update_peer_list(self.discovery.peers)

        # 選中這個節點
        self.selected_peer_ip = ip
        self.selected_peer_name = hostname
        self.target_label.config(text=f"{hostname} ({ip})")
        self._load_chat_history()

        # 在列表中選中
        for i in range(self.peer_listbox.size()):
            if ip in self.peer_listbox.get(i):
                self.peer_listbox.selection_clear(0, tk.END)
                self.peer_listbox.selection_set(i)
                break

        self._log(f"已連接: {hostname} ({ip})")

    def _on_peer_update(self, peers: dict):
        """節點列表更新回調"""
        self.root.after(0, lambda: self._update_peer_list(peers))

    def _ensure_peer_exists(self, ip: str, hostname: str, platform: str):
        """確保節點存在於列表中，如果不存在則自動添加"""
        if ip not in self.discovery.peers:
            new_peer = PeerInfo(ip, hostname, platform)
            new_peer.is_reachable = True
            self.discovery.peers[ip] = new_peer
            self._log(f"自動添加節點: {hostname} ({ip})")
            self._update_peer_list(self.discovery.peers)

            # 同時添加到最近連線
            self.recent_connections.add_connection(ip, hostname, platform)
            self._load_recent_connections()
        else:
            self.discovery.peers[ip].last_seen = time.time()

    def _update_peer_list(self, peers: dict):
        """更新節點列表"""
        current_selection = self.selected_peer_ip

        self.peer_listbox.delete(0, tk.END)

        for ip, peer in peers.items():
            status = "●" if peer.is_reachable else "○"
            ping_str = f"{peer.ping_ms:.0f}ms" if peer.ping_ms else "---"
            os_icon = "L" if "Linux" in peer.platform else "W" if "Windows" in peer.platform else "?"
            display = f"{status} [{os_icon}] {peer.hostname} ({ip}) [{ping_str}]"
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
                hostname_match = re.search(r'\]\s+(.+?)\s+\(', item)
                self.selected_peer_name = hostname_match.group(1) if hostname_match else self.selected_peer_ip
                self.target_label.config(text=f"{self.selected_peer_name} ({self.selected_peer_ip})")
                self._log(f"已選擇: {self.selected_peer_name}")
                self._load_chat_history()

                # 更新最近連線
                if self.selected_peer_ip in self.discovery.peers:
                    peer = self.discovery.peers[self.selected_peer_ip]
                    self.recent_connections.add_connection(
                        self.selected_peer_ip,
                        peer.hostname,
                        peer.platform
                    )
                    self._load_recent_connections()

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
        """清除聊天記錄 - 只清除對話，不移除節點"""
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

    def _refresh_peers(self):
        """重新掃描節點 - 不清除最近連線"""
        self._log("正在重新掃描網路...")
        # 保存當前選擇
        current_selection = self.selected_peer_ip

        # 清除發現的節點
        self.discovery.peers.clear()
        self._update_peer_list({})

        # 恢復選擇狀態
        if current_selection:
            self.selected_peer_ip = current_selection

    def _manual_add_ip(self):
        """手動添加 IP 地址 - 自動建立連線"""
        ip = simpledialog.askstring("手動添加 IP", "請輸入目標電腦的 IP 地址:", parent=self.root)

        if ip and ip.strip():
            ip = ip.strip()
            self._log(f"正在嘗試連接 {ip}...")

            def try_connect():
                ping_result = self.discovery.manual_ping(ip)
                hostname = f"PC-{ip.split('.')[-1]}"
                platform = "Unknown"

                peer = PeerInfo(ip, hostname, platform)
                peer.ping_ms = ping_result
                peer.is_reachable = ping_result is not None
                self.discovery.peers[ip] = peer

                if ping_result:
                    self._log(f"成功添加 {ip} (Ping: {ping_result:.1f}ms)")
                else:
                    self._log(f"已添加 {ip} (無法 Ping，但仍可嘗試連接)")

                # 更新 UI
                self.root.after(0, lambda: self._update_peer_list(self.discovery.peers))

                # 保存到最近連線
                self.recent_connections.add_connection(ip, hostname, platform)
                self.root.after(0, self._load_recent_connections)

                # 自動選中這個節點
                self.root.after(100, lambda: self._add_and_select_peer(ip, hostname, platform))

            threading.Thread(target=try_connect, daemon=True).start()

    def _show_diagnostic(self):
        """顯示診斷視窗"""
        diag_window = tk.Toplevel(self.root)
        diag_window.title("網路診斷")
        diag_window.geometry("700x550")
        diag_window.transient(self.root)
        diag_window.configure(bg=COLORS["bg_dark"])

        result_text = scrolledtext.ScrolledText(
            diag_window,
            font=('Consolas', 10),
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"]
        )
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        guide = self.diagnostic.get_quick_setup_guide()
        result_text.insert(tk.END, guide)
        result_text.insert(tk.END, "\n\n正在執行診斷...\n")

        btn_frame = tk.Frame(diag_window, bg=COLORS["bg_dark"])
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

                network_type = results.get("network_type", {})
                if network_type.get("is_public"):
                    result_text.insert(tk.END, "⚠ " + "=" * 56 + " ⚠\n")
                    result_text.insert(tk.END, f"  {network_type.get('warning', '警告: 公共網路!')}\n")
                    result_text.insert(tk.END, "⚠ " + "=" * 56 + " ⚠\n\n")
                else:
                    network_name = network_type.get("network_name", "Unknown")
                    result_text.insert(tk.END, f"網路: {network_name} (私人網路)\n")

                sys_info = results.get("system_info", {})
                result_text.insert(tk.END, f"作業系統: {sys_info.get('os', 'Unknown')}\n")

                fw = results.get("firewall_status", {})
                software = fw.get("software", {})
                detected = software.get("detected", [])
                provider = software.get("firewall_provider", "Unknown")

                result_text.insert(tk.END, f"\n安全軟件/防火牆:\n")
                for sw in detected:
                    result_text.insert(tk.END, f"  * {sw}\n")
                result_text.insert(tk.END, f"  主要防火牆: {provider}\n")

                ports = results.get("port_status", {})
                result_text.insert(tk.END, f"\n端口狀態:\n")

                udp_in_use = ports.get('udp_52525_in_use', False)
                udp_process = ports.get('udp_52525_process')
                if udp_in_use:
                    if udp_process:
                        result_text.insert(tk.END, f"  UDP 52525: 使用中 - {udp_process}\n")
                    else:
                        result_text.insert(tk.END, f"  UDP 52525: 使用中 (PCPCS)\n")
                else:
                    result_text.insert(tk.END, f"  UDP 52525: 可用\n")

                tcp_in_use = ports.get('tcp_52526_in_use', False)
                tcp_process = ports.get('tcp_52526_process')
                if tcp_in_use:
                    if tcp_process:
                        result_text.insert(tk.END, f"  TCP 52526: 使用中 - {tcp_process}\n")
                    else:
                        result_text.insert(tk.END, f"  TCP 52526: 使用中 (PCPCS)\n")
                else:
                    result_text.insert(tk.END, f"  TCP 52526: 可用\n")

                conn = results.get("connectivity")
                if conn:
                    result_text.insert(tk.END, f"\n連接測試 ({target}):\n")
                    result_text.insert(tk.END, f"  Ping: {'成功' if conn.get('ping') else '失敗'}")
                    if conn.get('ping_ms'):
                        result_text.insert(tk.END, f" ({conn['ping_ms']:.1f}ms)")
                    result_text.insert(tk.END, f"\n  TCP 52526: {'連通' if conn.get('tcp_52526') else '不通'}\n")

                result_text.insert(tk.END, "\n" + "=" * 60 + "\n")
                result_text.insert(tk.END, "建議:\n")
                result_text.insert(tk.END, "=" * 60 + "\n\n")

                for rec in results.get("recommendations", []):
                    result_text.insert(tk.END, f"* {rec['issue']}\n")
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
        ttk.Button(btn_frame, text="關閉", command=diag_window.destroy,
                  style='Secondary.TButton').pack(side=tk.RIGHT)

        diag_window.after(100, run_diagnostic)

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
