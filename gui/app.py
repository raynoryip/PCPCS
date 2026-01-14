"""
PCPCS GUI 介面
使用 Tkinter 實作跨平台圖形介面
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
        import socket
        info = {
            "local_ip": self.local_ip,
            "hostname": self.hostname,
            "discovery_port": 52525,
            "transfer_port": 52526
        }

        # 取得所有網路介面
        try:
            interfaces = []
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
            "udp_52525_in_use": False,
            "tcp_52526_in_use": False
        }

        # 檢查 UDP 52525
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 52525))
            sock.close()
            results["udp_52525"] = True  # 端口空閒
        except OSError as e:
            err_str = str(e)
            if "Address already in use" in err_str or "Only one usage" in err_str or "10048" in err_str:
                results["udp_52525"] = True  # 端口可用，只是已被使用
                results["udp_52525_in_use"] = True

        # 檢查 TCP 52526
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 52526))
            sock.close()
            results["tcp_52526"] = True  # 端口空閒
        except OSError as e:
            err_str = str(e)
            if "Address already in use" in err_str or "Only one usage" in err_str or "10048" in err_str:
                results["tcp_52526"] = True  # 端口可用，只是已被使用
                results["tcp_52526_in_use"] = True

        return results

    def _detect_security_software(self) -> dict:
        """檢測安裝的安全軟件/防火牆"""
        import subprocess
        result = {
            "detected": [],
            "firewall_provider": "Unknown"
        }

        # 常見安全軟件的進程名和顯示名稱
        security_software = {
            # 進程名: 顯示名稱
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
                # 使用 WMIC 查詢防病毒軟件
                try:
                    proc = subprocess.run(
                        ["wmic", "/namespace:\\\\root\\SecurityCenter2", "path",
                         "AntiVirusProduct", "get", "displayName"],
                        capture_output=True, text=True, timeout=10
                    )
                    if proc.returncode == 0:
                        lines = proc.stdout.strip().split('\n')
                        for line in lines[1:]:  # 跳過標題行
                            name = line.strip()
                            if name and name != "displayName":
                                result["detected"].append(name)
                                if result["firewall_provider"] == "Unknown":
                                    result["firewall_provider"] = name
                except:
                    pass

                # 也檢查防火牆產品
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

                # 備用方法：掃描進程
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
                # Linux 主要用 UFW 或 iptables
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

                # 檢查是否有 ClamAV
                try:
                    proc = subprocess.run(["which", "clamscan"], capture_output=True, timeout=5)
                    if proc.returncode == 0:
                        result["detected"].append("ClamAV")
                except:
                    pass

        except Exception as e:
            result["error"] = str(e)

        # 如果沒檢測到，標記為系統內建
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
                # 檢查 Windows 防火牆
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
                # 檢查 UFW
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
                # 解析延遲
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

        # 取得檢測到的防火牆軟件
        fw = results.get("firewall_status", {})
        software = fw.get("software", {})
        provider = software.get("firewall_provider", "Unknown")
        detected = software.get("detected", [])

        # 根據不同防火牆軟件生成特定建議
        if self.system == "Windows":
            # 第三方防火牆特定建議
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
                        "   - Remote Address: 不要限制 (留空或 Any)",
                        "",
                        "注意: Custom Remote Address 設定 192.168.1.0/24 可能導致",
                        "無法接收來自其他子網的 UDP 廣播，建議移除此限制"
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
                "McAfee": {
                    "issue": f"檢測到 McAfee 防火牆",
                    "solution": "在 McAfee 中允許 PCPCS:",
                    "commands": [
                        "1. 開啟 McAfee → Firewall",
                        "2. 點擊 Internet Connections for Programs",
                        "3. 找到 python.exe 並設為 Allow All",
                        "4. 或添加端口規則: UDP 52525, TCP 52526"
                    ]
                },
                "Kaspersky": {
                    "issue": f"檢測到 Kaspersky 防火牆",
                    "solution": "在 Kaspersky 中允許 PCPCS:",
                    "commands": [
                        "1. 開啟 Kaspersky → Settings → Protection → Firewall",
                        "2. 點擊 Configure application rules",
                        "3. 找到 python.exe 並設為 Trusted",
                        "4. 或在 Packet rules 中添加允許規則"
                    ]
                },
                "ESET": {
                    "issue": f"檢測到 ESET 防火牆",
                    "solution": "在 ESET 中允許 PCPCS:",
                    "commands": [
                        "1. 開啟 ESET → Setup → Network protection → Firewall",
                        "2. 點擊 Configure → Rules",
                        "3. 添加規則允許 python.exe",
                        "4. 設定方向為 Both，端口為 52525 和 52526"
                    ]
                },
                "Avast": {
                    "issue": f"檢測到 Avast 防火牆",
                    "solution": "在 Avast 中允許 PCPCS:",
                    "commands": [
                        "1. 開啟 Avast → Protection → Firewall",
                        "2. 點擊 Application settings",
                        "3. 找到 python.exe 並設為 Allow",
                        "4. 或在 Firewall rules 中添加端口規則"
                    ]
                },
                "Windows Defender": {
                    "issue": "使用 Windows Defender 防火牆",
                    "solution": "在 Windows Defender 中開放端口 (以管理員身份執行):",
                    "commands": [
                        'netsh advfirewall firewall add rule name="PCPCS UDP" dir=in action=allow protocol=UDP localport=52525',
                        'netsh advfirewall firewall add rule name="PCPCS TCP" dir=in action=allow protocol=TCP localport=52526',
                        "",
                        "或手動設定:",
                        "1. 開啟 Windows Defender 防火牆 → 進階設定",
                        "2. 點擊 輸入規則 → 新增規則",
                        "3. 選擇 連接埠 → UDP → 特定本機連接埠: 52525",
                        "4. 允許連線 → 套用到所有設定檔 → 命名為 PCPCS UDP",
                        "5. 重複以上步驟添加 TCP 52526"
                    ]
                }
            }

            # 檢查是否有匹配的第三方防火牆
            for sw in detected:
                for key, guide in third_party_guides.items():
                    if key.lower() in sw.lower():
                        recommendations.append(guide)
                        break

            # 如果沒有找到特定指南，添加通用 Windows 建議
            if not recommendations:
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

        # 連接測試建議
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
║                                                               ║
║ 如果使用第三方防火牆(如 Bitdefender):                         ║
║   請在防火牆設定中允許 python.exe 的所有連線                  ║
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
        self.root.title(f"PCPCS - {get_hostname()} ({get_local_ip()})")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        # 設定樣式
        self.style = ttk.Style()
        self._setup_styles()

        # 聊天記錄管理
        self.chat_history = ChatHistory()

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

    def _setup_styles(self):
        """設定 UI 樣式"""
        self.style.configure('Title.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('Status.TLabel', font=('Helvetica', 9))
        self.style.configure('Chat.TFrame', relief='sunken')

    def _create_ui(self):
        """建立使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側 - 節點列表和控制
        left_frame = ttk.Frame(main_frame, width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        # 節點列表框
        peer_frame = ttk.LabelFrame(left_frame, text="已發現的電腦", padding="5")
        peer_frame.pack(fill=tk.BOTH, expand=True)

        self.peer_listbox = tk.Listbox(peer_frame, font=('Consolas', 9), selectbackground='#4a90d9')
        self.peer_listbox.pack(fill=tk.BOTH, expand=True)
        self.peer_listbox.bind('<<ListboxSelect>>', self._on_peer_select)

        # 按鈕框
        btn_frame = ttk.Frame(peer_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="重新掃描", command=self._refresh_peers).pack(fill=tk.X, pady=1)
        ttk.Button(btn_frame, text="手動添加 IP", command=self._manual_add_ip).pack(fill=tk.X, pady=1)
        ttk.Button(btn_frame, text="測試連接", command=self._manual_ping).pack(fill=tk.X, pady=1)
        ttk.Button(btn_frame, text="網路診斷", command=self._show_diagnostic).pack(fill=tk.X, pady=1)

        # 本機資訊
        info_frame = ttk.LabelFrame(left_frame, text="本機資訊", padding="5")
        info_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(info_frame, text=f"名稱: {get_hostname()}", font=('Consolas', 9)).pack(anchor='w')
        ttk.Label(info_frame, text=f"IP: {get_local_ip()}", font=('Consolas', 9)).pack(anchor='w')
        ttk.Label(info_frame, text=f"發現端口: UDP 52525", font=('Consolas', 9)).pack(anchor='w')
        ttk.Label(info_frame, text=f"傳輸端口: TCP 52526", font=('Consolas', 9)).pack(anchor='w')

        # 右側 - 聊天和傳輸區
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 目標顯示
        target_frame = ttk.Frame(right_frame)
        target_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(target_frame, text="對話對象:", style='Title.TLabel').pack(side=tk.LEFT)
        self.target_label = ttk.Label(target_frame, text="(請從左側選擇電腦)", font=('Helvetica', 10))
        self.target_label.pack(side=tk.LEFT, padx=(10, 0))

        # 聊天對話框
        chat_frame = ttk.LabelFrame(right_frame, text="對話", padding="5")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 聊天記錄顯示區
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, height=15, font=('Consolas', 10),
            state='disabled', wrap=tk.WORD
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # 設定聊天顯示的標籤樣式
        self.chat_display.tag_configure('self', foreground='#2e7d32', font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('peer', foreground='#1565c0', font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('system', foreground='#757575', font=('Consolas', 9, 'italic'))
        self.chat_display.tag_configure('file', foreground='#6a1b9a', font=('Consolas', 10))
        self.chat_display.tag_configure('timestamp', foreground='#9e9e9e', font=('Consolas', 8))

        # 輸入區
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))

        self.message_input = ttk.Entry(input_frame, font=('Consolas', 11))
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_input.bind('<Return>', lambda e: self._send_text())

        self.send_btn = ttk.Button(input_frame, text="發送", command=self._send_text, width=8)
        self.send_btn.pack(side=tk.LEFT)

        # 聊天控制按鈕
        chat_btn_frame = ttk.Frame(chat_frame)
        chat_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(chat_btn_frame, text="清除記錄", command=self._clear_chat_history).pack(side=tk.LEFT)
        ttk.Button(chat_btn_frame, text="開啟記錄資料夾", command=self._open_data_folder).pack(side=tk.LEFT, padx=5)

        # 檔案傳輸區
        file_frame = ttk.LabelFrame(right_frame, text="檔案傳輸", padding="5")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=tk.X)

        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_select_frame, textvariable=self.file_path_var, font=('Consolas', 10))
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(file_select_frame, text="選擇", command=self._browse_file).pack(side=tk.LEFT, padx=(0, 5))
        self.send_file_btn = ttk.Button(file_select_frame, text="發送檔案", command=self._send_file)
        self.send_file_btn.pack(side=tk.LEFT)

        # 進度條
        progress_frame = ttk.Frame(file_frame)
        progress_frame.pack(fill=tk.X, pady=(5, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(progress_frame, text="", font=('Consolas', 9))
        self.progress_label.pack(anchor='w')

        # 系統日誌
        log_frame = ttk.LabelFrame(right_frame, text="系統日誌", padding="5")
        log_frame.pack(fill=tk.X)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=4, font=('Consolas', 8), state='disabled')
        self.log_text.pack(fill=tk.X)

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
            os_icon = "🐧" if "Linux" in peer.platform else "🪟" if "Windows" in peer.platform else "💻"
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
            # 解析 IP - 格式: "● 🐧 hostname (ip) [ping]"
            import re
            match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', item)
            if match:
                self.selected_peer_ip = match.group(1)
                # 解析 hostname
                hostname_match = re.search(r'[●○]\s+.\s+(.+?)\s+\(', item)
                self.selected_peer_name = hostname_match.group(1) if hostname_match else self.selected_peer_ip
                self.target_label.config(text=f"{self.selected_peer_name} ({self.selected_peer_ip})")
                self._log(f"已選擇: {self.selected_peer_name}")
                # 載入聊天記錄
                self._load_chat_history()

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

        # 儲存到記錄
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
            f"確定要清除與 {self.selected_peer_name} 的所有聊天記錄嗎?\n此操作無法復原。"
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
                peer = PeerInfo(ip, f"Manual-{ip}", "Unknown")
                peer.ping_ms = ping_result
                peer.is_reachable = ping_result is not None
                self.discovery.peers[ip] = peer

                if ping_result:
                    self._log(f"成功添加 {ip} (Ping: {ping_result:.1f}ms)")
                else:
                    self._log(f"已添加 {ip} (無法 Ping)")

                self.root.after(0, lambda: self._update_peer_list(self.discovery.peers))

            threading.Thread(target=try_connect, daemon=True).start()

    def _show_diagnostic(self):
        """顯示診斷視窗"""
        diag_window = tk.Toplevel(self.root)
        diag_window.title("網路診斷")
        diag_window.geometry("700x550")
        diag_window.transient(self.root)

        # 診斷結果顯示
        result_text = scrolledtext.ScrolledText(diag_window, font=('Consolas', 10))
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顯示基本指南
        guide = self.diagnostic.get_quick_setup_guide()
        result_text.insert(tk.END, guide)
        result_text.insert(tk.END, "\n\n正在執行診斷...\n")

        btn_frame = ttk.Frame(diag_window)
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

                # 系統資訊
                sys_info = results.get("system_info", {})
                result_text.insert(tk.END, f"作業系統: {sys_info.get('os', 'Unknown')} {sys_info.get('os_version', '')[:30]}\n")

                # 安全軟件檢測
                fw = results.get("firewall_status", {})
                software = fw.get("software", {})
                detected = software.get("detected", [])
                provider = software.get("firewall_provider", "Unknown")

                result_text.insert(tk.END, f"\n安全軟件/防火牆:\n")
                if detected:
                    for sw in detected:
                        result_text.insert(tk.END, f"  ✓ {sw}\n")
                else:
                    result_text.insert(tk.END, f"  未檢測到第三方安全軟件\n")
                result_text.insert(tk.END, f"  主要防火牆: {provider}\n")

                # 端口狀態 - 更清楚的說明
                ports = results.get("port_status", {})
                result_text.insert(tk.END, f"\n端口狀態 (本機):\n")

                udp_status = ports.get('udp_52525')
                udp_in_use = ports.get('udp_52525_in_use', False)
                if udp_status:
                    if udp_in_use:
                        result_text.insert(tk.END, f"  UDP 52525: ✓ PCPCS 正在監聽中 (正常)\n")
                    else:
                        result_text.insert(tk.END, f"  UDP 52525: ✓ 端口可用\n")
                else:
                    result_text.insert(tk.END, f"  UDP 52525: ✗ 無法使用\n")

                tcp_status = ports.get('tcp_52526')
                tcp_in_use = ports.get('tcp_52526_in_use', False)
                if tcp_status:
                    if tcp_in_use:
                        result_text.insert(tk.END, f"  TCP 52526: ✓ PCPCS 正在監聽中 (正常)\n")
                    else:
                        result_text.insert(tk.END, f"  TCP 52526: ✓ 端口可用\n")
                else:
                    result_text.insert(tk.END, f"  TCP 52526: ✗ 無法使用\n")

                # 防火牆狀態
                result_text.insert(tk.END, f"\n防火牆狀態: {fw.get('status', 'unknown')}\n")
                if fw.get('pcpcs_allowed') == 'yes':
                    result_text.insert(tk.END, f"  PCPCS 端口規則: ✓ 已設定\n")
                elif fw.get('pcpcs_allowed') == 'no':
                    result_text.insert(tk.END, f"  PCPCS 端口規則: ✗ 未設定\n")

                # 連接測試
                conn = results.get("connectivity")
                if conn:
                    result_text.insert(tk.END, f"\n連接測試 ({target}):\n")
                    result_text.insert(tk.END, f"  Ping: {'✓ 成功' if conn.get('ping') else '✗ 失敗'}")
                    if conn.get('ping_ms'):
                        result_text.insert(tk.END, f" ({conn['ping_ms']:.1f}ms)")
                    result_text.insert(tk.END, f"\n  TCP 52526: {'✓ 連通' if conn.get('tcp_52526') else '✗ 不通'}\n")

                # 建議
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

        ttk.Button(btn_frame, text="重新診斷", command=run_diagnostic).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="複製資訊", command=lambda: self._copy_to_clipboard(result_text.get('1.0', tk.END))).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="關閉", command=diag_window.destroy).pack(side=tk.RIGHT)

        # 自動執行診斷
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

        # 計算速度
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

        # 計算傳輸速度
        speed_str = ""
        if self.transfer_start_time and self.transfer_size > 0 and success:
            elapsed = time.time() - self.transfer_start_time
            if elapsed > 0:
                speed = self.transfer_size / elapsed
                speed_str = f"{self._format_size(speed)}/s"

        self.progress_label.config(text=message)

        if success:
            self._log(f"發送成功 {speed_str}")
            # 如果是檔案傳輸，添加到聊天記錄
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

    def _on_text_received(self, sender_ip: str, sender_name: str, text: str):
        """收到文字回調"""
        self.root.after(0, lambda: self._handle_text_received(sender_ip, sender_name, text))

    def _handle_text_received(self, sender_ip: str, sender_name: str, text: str):
        """處理收到的文字"""
        # 如果目前選擇的就是發送者，直接顯示在聊天框
        if self.selected_peer_ip == sender_ip:
            self._add_chat_message(sender_name, text)
        else:
            # 儲存到該 IP 的聊天記錄
            self.chat_history.save_message(sender_ip, sender_name, text)
            # 顯示系統通知
            self.chat_display.config(state='normal')
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
            self.chat_display.insert(tk.END, f"收到來自 {sender_name} ({sender_ip}) 的新訊息\n", 'system')
            self.chat_display.see(tk.END)
            self.chat_display.config(state='disabled')

        # 複製到剪貼簿
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._log(f"收到文字 (已複製到剪貼簿)")

    def _on_file_received(self, sender_ip: str, sender_name: str, filepath: str, filesize: int):
        """收到檔案回調"""
        self.root.after(0, lambda: self._handle_file_received(sender_ip, sender_name, filepath, filesize))

    def _handle_file_received(self, sender_ip: str, sender_name: str, filepath: str, filesize: int):
        """處理收到的檔案"""
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
    app = PCPCSApp()
    app.run()


if __name__ == "__main__":
    main()
