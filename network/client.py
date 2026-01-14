"""
TCP 傳輸客戶端
負責發送文字和檔案到其他節點
"""
import socket
import json
import os
import threading
from typing import Callable, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    TRANSFER_PORT, BUFFER_SIZE, FILE_CHUNK_SIZE,
    MSG_TYPE_TEXT, MSG_TYPE_FILE,
    get_hostname
)


class TransferClient:
    """傳輸發送客戶端"""

    def __init__(self,
                 on_progress: Optional[Callable] = None,
                 on_status: Optional[Callable] = None,
                 on_complete: Optional[Callable] = None):
        self.on_progress = on_progress
        self.on_status = on_status
        self.on_complete = on_complete
        self.hostname = get_hostname()

    def _log(self, message: str):
        """輸出狀態訊息"""
        if self.on_status:
            self.on_status(message)
        else:
            print(message)

    def send_text(self, target_ip: str, text: str) -> bool:
        """
        發送文字訊息
        """
        def _send():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((target_ip, TRANSFER_PORT))

                # 準備標頭
                text_bytes = text.encode('utf-8')
                header = {
                    "type": MSG_TYPE_TEXT,
                    "sender": self.hostname,
                    "length": len(text_bytes)
                }
                header_json = json.dumps(header).encode('utf-8')

                # 發送標頭長度 + 標頭 + 內容
                sock.send(len(header_json).to_bytes(4, 'big'))
                sock.send(header_json)
                sock.send(text_bytes)

                # 等待確認
                response = sock.recv(BUFFER_SIZE)
                sock.close()

                if response == b"OK":
                    self._log(f"文字訊息已發送到 {target_ip}")
                    if self.on_complete:
                        self.on_complete(True, "文字發送成功")
                    return True
                else:
                    self._log(f"發送失敗: 未收到確認")
                    if self.on_complete:
                        self.on_complete(False, "未收到確認")
                    return False

            except Exception as e:
                self._log(f"發送文字失敗: {e}")
                if self.on_complete:
                    self.on_complete(False, str(e))
                return False

        # 在新線程中執行
        thread = threading.Thread(target=_send, daemon=True)
        thread.start()
        return True

    def send_file(self, target_ip: str, filepath: str) -> bool:
        """
        發送檔案
        """
        if not os.path.exists(filepath):
            self._log(f"檔案不存在: {filepath}")
            if self.on_complete:
                self.on_complete(False, "檔案不存在")
            return False

        def _send():
            try:
                filesize = os.path.getsize(filepath)
                filename = os.path.basename(filepath)

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(30)
                sock.connect((target_ip, TRANSFER_PORT))

                # 準備標頭
                header = {
                    "type": MSG_TYPE_FILE,
                    "sender": self.hostname,
                    "filename": filename,
                    "filesize": filesize
                }
                header_json = json.dumps(header).encode('utf-8')

                # 發送標頭
                sock.send(len(header_json).to_bytes(4, 'big'))
                sock.send(header_json)

                self._log(f"開始發送檔案: {filename} ({filesize} bytes)")

                # 發送檔案內容
                sent = 0
                with open(filepath, 'rb') as f:
                    while sent < filesize:
                        chunk = f.read(FILE_CHUNK_SIZE)
                        if not chunk:
                            break
                        sock.send(chunk)
                        sent += len(chunk)

                        # 更新進度
                        if self.on_progress:
                            progress = (sent / filesize) * 100
                            self.on_progress(progress, f"發送中: {filename}")

                # 等待確認
                sock.settimeout(30)
                response = sock.recv(BUFFER_SIZE)
                sock.close()

                if response == b"OK":
                    self._log(f"檔案已發送到 {target_ip}")
                    if self.on_complete:
                        self.on_complete(True, f"檔案 {filename} 發送成功")
                    return True
                else:
                    self._log(f"發送失敗: 未收到確認")
                    if self.on_complete:
                        self.on_complete(False, "未收到確認")
                    return False

            except Exception as e:
                self._log(f"發送檔案失敗: {e}")
                if self.on_complete:
                    self.on_complete(False, str(e))
                return False

        # 在新線程中執行
        thread = threading.Thread(target=_send, daemon=True)
        thread.start()
        return True


if __name__ == "__main__":
    # 測試代碼
    client = TransferClient(
        on_progress=lambda p, m: print(f"進度: {p:.1f}% - {m}"),
        on_status=print,
        on_complete=lambda ok, msg: print(f"完成: {ok} - {msg}")
    )

    import sys
    if len(sys.argv) > 2:
        target = sys.argv[1]
        if sys.argv[2] == "text":
            client.send_text(target, "Hello from PCPCS!")
        else:
            client.send_file(target, sys.argv[2])

        import time
        time.sleep(5)
