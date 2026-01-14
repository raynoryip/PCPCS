"""
網路發現模組
使用 UDP 廣播自動發現區域網路內的其他 PCPCS 節點
包含 Ping 測試功能
"""
import socket
import json
import threading
import time
import subprocess
import platform
from typing import Dict, Callable, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    DISCOVERY_PORT, BROADCAST_INTERVAL, PING_TIMEOUT,
    MSG_TYPE_DISCOVERY, MSG_TYPE_RESPONSE,
    get_hostname, get_platform, get_local_ip
)


class PeerInfo:
    """節點資訊類"""
    def __init__(self, ip: str, hostname: str, platform_name: str):
        self.ip = ip
        self.hostname = hostname
        self.platform = platform_name
        self.last_seen = time.time()
        self.ping_ms: Optional[float] = None
        self.is_reachable = False

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "hostname": self.hostname,
            "platform": self.platform,
            "ping_ms": self.ping_ms,
            "is_reachable": self.is_reachable
        }

    def __str__(self):
        status = f"{self.ping_ms:.1f}ms" if self.ping_ms else "N/A"
        return f"{self.hostname} ({self.ip}) [{self.platform}] - {status}"


class NetworkDiscovery:
    """網路發現服務"""

    def __init__(self, on_peer_update: Optional[Callable] = None):
        self.peers: Dict[str, PeerInfo] = {}
        self.on_peer_update = on_peer_update
        self.running = False
        self.local_ip = get_local_ip()
        self.hostname = get_hostname()
        self.platform_name = get_platform()

        self._broadcast_thread: Optional[threading.Thread] = None
        self._listen_thread: Optional[threading.Thread] = None
        self._ping_thread: Optional[threading.Thread] = None

    def start(self):
        """啟動發現服務"""
        self.running = True

        # 啟動廣播線程
        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._broadcast_thread.start()

        # 啟動監聽線程
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

        # 啟動 Ping 測試線程
        self._ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self._ping_thread.start()

    def stop(self):
        """停止發現服務"""
        self.running = False

    def _broadcast_loop(self):
        """廣播循環 - 定期發送發現訊息"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)

        message = json.dumps({
            "type": MSG_TYPE_DISCOVERY,
            "hostname": self.hostname,
            "platform": self.platform_name,
            "ip": self.local_ip
        }).encode('utf-8')

        while self.running:
            try:
                sock.sendto(message, ('<broadcast>', DISCOVERY_PORT))
            except Exception as e:
                print(f"廣播錯誤: {e}")
            time.sleep(BROADCAST_INTERVAL)

        sock.close()

    def _listen_loop(self):
        """監聽循環 - 接收其他節點的發現訊息"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind(('', DISCOVERY_PORT))
        except Exception as e:
            print(f"綁定端口失敗: {e}")
            return

        sock.settimeout(1)

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                self._handle_discovery_message(data, addr[0])
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"監聽錯誤: {e}")

        sock.close()

    def _handle_discovery_message(self, data: bytes, sender_ip: str):
        """處理發現訊息"""
        try:
            message = json.loads(data.decode('utf-8'))

            # 忽略自己的訊息
            if sender_ip == self.local_ip:
                return

            msg_type = message.get("type")

            if msg_type in [MSG_TYPE_DISCOVERY, MSG_TYPE_RESPONSE]:
                hostname = message.get("hostname", "Unknown")
                platform_name = message.get("platform", "Unknown")

                # 更新或新增節點
                if sender_ip not in self.peers:
                    self.peers[sender_ip] = PeerInfo(sender_ip, hostname, platform_name)
                    # 發送回應
                    if msg_type == MSG_TYPE_DISCOVERY:
                        self._send_response(sender_ip)
                else:
                    self.peers[sender_ip].last_seen = time.time()

                # 觸發更新回調
                if self.on_peer_update:
                    self.on_peer_update(self.peers)

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"處理訊息錯誤: {e}")

    def _send_response(self, target_ip: str):
        """發送回應訊息"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = json.dumps({
                "type": MSG_TYPE_RESPONSE,
                "hostname": self.hostname,
                "platform": self.platform_name,
                "ip": self.local_ip
            }).encode('utf-8')
            sock.sendto(message, (target_ip, DISCOVERY_PORT))
            sock.close()
        except Exception as e:
            print(f"發送回應錯誤: {e}")

    def _ping_loop(self):
        """Ping 測試循環 - 定期測試節點連接狀態"""
        while self.running:
            peers_to_ping = list(self.peers.keys())

            for ip in peers_to_ping:
                if not self.running:
                    break
                if ip in self.peers:
                    ping_result = self._ping_host(ip)
                    self.peers[ip].ping_ms = ping_result
                    self.peers[ip].is_reachable = ping_result is not None

            # 清理超時節點 (超過 30 秒未見)
            current_time = time.time()
            expired = [ip for ip, peer in self.peers.items()
                      if current_time - peer.last_seen > 30]
            for ip in expired:
                del self.peers[ip]

            if self.on_peer_update and (peers_to_ping or expired):
                self.on_peer_update(self.peers)

            time.sleep(5)  # 每 5 秒測試一次

    def _ping_host(self, ip: str) -> Optional[float]:
        """Ping 指定主機，返回延遲(ms)或 None"""
        try:
            system = platform.system().lower()

            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", str(PING_TIMEOUT * 1000), ip]
            else:  # Linux/Mac
                cmd = ["ping", "-c", "1", "-W", str(PING_TIMEOUT), ip]

            start_time = time.time()
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=PING_TIMEOUT + 1
            )
            end_time = time.time()

            if result.returncode == 0:
                # 嘗試從輸出解析實際延遲
                output = result.stdout.decode('utf-8', errors='ignore')

                # Windows 格式: "時間=XXms" 或 "time=XXms"
                # Linux 格式: "time=XX.X ms"
                import re
                match = re.search(r'[時间time][=<][\s]*([0-9.]+)\s*ms', output, re.IGNORECASE)
                if match:
                    return float(match.group(1))

                # 如果無法解析，使用計算的時間
                return (end_time - start_time) * 1000

            return None

        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(f"Ping 錯誤 {ip}: {e}")
            return None

    def get_peers(self) -> Dict[str, PeerInfo]:
        """取得所有已發現的節點"""
        return self.peers.copy()

    def manual_ping(self, ip: str) -> Optional[float]:
        """手動 Ping 指定 IP"""
        return self._ping_host(ip)


if __name__ == "__main__":
    # 測試代碼
    def on_update(peers):
        print(f"\n發現 {len(peers)} 個節點:")
        for ip, peer in peers.items():
            print(f"  - {peer}")

    discovery = NetworkDiscovery(on_peer_update=on_update)
    print(f"本機: {discovery.hostname} ({discovery.local_ip})")
    print("開始發現網路節點...")
    discovery.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止服務...")
        discovery.stop()
