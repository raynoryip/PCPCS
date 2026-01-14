"""
TCP 接收伺服器
負責接收來自其他節點的文字和檔案
"""
import socket
import json
import threading
import os
from typing import Callable, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    TRANSFER_PORT, BUFFER_SIZE, FILE_CHUNK_SIZE, RECEIVE_DIR,
    MSG_TYPE_TEXT, MSG_TYPE_FILE, MSG_TYPE_FILE_CHUNK, MSG_TYPE_FILE_END
)


class TransferServer:
    """傳輸接收伺服器"""

    def __init__(self,
                 on_text_received: Optional[Callable] = None,
                 on_file_received: Optional[Callable] = None,
                 on_progress: Optional[Callable] = None,
                 on_status: Optional[Callable] = None):
        self.on_text_received = on_text_received
        self.on_file_received = on_file_received
        self.on_progress = on_progress
        self.on_status = on_status

        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self._server_thread: Optional[threading.Thread] = None

        # 確保接收目錄存在
        os.makedirs(RECEIVE_DIR, exist_ok=True)

    def start(self):
        """啟動伺服器"""
        self.running = True
        self._server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self._server_thread.start()

    def stop(self):
        """停止伺服器"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

    def _log(self, message: str):
        """輸出狀態訊息"""
        if self.on_status:
            self.on_status(message)
        else:
            print(message)

    def _server_loop(self):
        """伺服器主循環"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind(('', TRANSFER_PORT))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1)
            self._log(f"傳輸伺服器已啟動，監聽端口 {TRANSFER_PORT}")

            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    self._log(f"接受來自 {addr[0]} 的連接")

                    # 為每個客戶端創建新線程
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr[0]),
                        daemon=True
                    )
                    client_thread.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self._log(f"接受連接錯誤: {e}")

        except Exception as e:
            self._log(f"伺服器啟動失敗: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def _handle_client(self, client_socket: socket.socket, client_ip: str):
        """處理客戶端連接"""
        try:
            # 接收標頭
            header_data = self._recv_exact(client_socket, 4)
            if not header_data:
                return

            header_length = int.from_bytes(header_data, 'big')
            header_json = self._recv_exact(client_socket, header_length)
            if not header_json:
                return

            header = json.loads(header_json.decode('utf-8'))
            msg_type = header.get("type")

            if msg_type == MSG_TYPE_TEXT:
                self._handle_text(client_socket, header, client_ip)
            elif msg_type == MSG_TYPE_FILE:
                self._handle_file(client_socket, header, client_ip)

            # 發送確認
            client_socket.send(b"OK")

        except Exception as e:
            self._log(f"處理客戶端錯誤: {e}")
        finally:
            client_socket.close()

    def _recv_exact(self, sock: socket.socket, size: int) -> Optional[bytes]:
        """精確接收指定大小的數據"""
        data = b''
        while len(data) < size:
            chunk = sock.recv(min(size - len(data), BUFFER_SIZE))
            if not chunk:
                return None
            data += chunk
        return data

    def _handle_text(self, sock: socket.socket, header: dict, sender_ip: str):
        """處理文字訊息"""
        text_length = header.get("length", 0)
        sender_name = header.get("sender", sender_ip)
        sender_platform = header.get("platform", "Unknown")

        text_data = self._recv_exact(sock, text_length)
        if text_data:
            text = text_data.decode('utf-8')
            self._log(f"收到來自 {sender_name} 的文字訊息")

            if self.on_text_received:
                self.on_text_received(sender_ip, sender_name, text, sender_platform)

    def _handle_file(self, sock: socket.socket, header: dict, sender_ip: str):
        """處理檔案傳輸"""
        filename = header.get("filename", "unknown_file")
        filesize = header.get("filesize", 0)
        sender_name = header.get("sender", sender_ip)
        sender_platform = header.get("platform", "Unknown")

        # 安全處理檔名，避免路徑穿越攻擊
        safe_filename = os.path.basename(filename)
        filepath = os.path.join(RECEIVE_DIR, safe_filename)

        # 如果檔案已存在，添加編號
        base, ext = os.path.splitext(safe_filename)
        counter = 1
        while os.path.exists(filepath):
            filepath = os.path.join(RECEIVE_DIR, f"{base}_{counter}{ext}")
            counter += 1

        self._log(f"開始接收檔案: {safe_filename} ({filesize} bytes)")

        received = 0
        try:
            with open(filepath, 'wb') as f:
                while received < filesize:
                    chunk_size = min(FILE_CHUNK_SIZE, filesize - received)
                    chunk = self._recv_exact(sock, chunk_size)
                    if not chunk:
                        raise Exception("連接中斷")

                    f.write(chunk)
                    received += len(chunk)

                    # 更新進度
                    if self.on_progress:
                        progress = (received / filesize) * 100
                        self.on_progress(progress, f"接收中: {safe_filename}")

            self._log(f"檔案接收完成: {filepath}")

            if self.on_file_received:
                self.on_file_received(sender_ip, sender_name, filepath, filesize, sender_platform)

        except Exception as e:
            self._log(f"檔案接收失敗: {e}")
            # 刪除不完整的檔案
            if os.path.exists(filepath):
                os.remove(filepath)


if __name__ == "__main__":
    def on_text(ip, name, text):
        print(f"[TEXT] {name}: {text}")

    def on_file(ip, name, path, size):
        print(f"[FILE] {name}: {path} ({size} bytes)")

    server = TransferServer(
        on_text_received=on_text,
        on_file_received=on_file,
        on_status=print
    )
    server.start()

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
