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
    MSG_TYPE_FOLDER_START, MSG_TYPE_FOLDER_FILE, MSG_TYPE_FOLDER_END,
    RESP_ACK, RESP_SKIP,
    get_hostname, get_platform
)
import hashlib


class TransferClient:
    """傳輸發送客戶端"""

    def __init__(self,
                 on_progress: Optional[Callable] = None,
                 on_status: Optional[Callable] = None,
                 on_complete: Optional[Callable] = None,
                 on_folder_progress: Optional[Callable] = None):
        self.on_progress = on_progress
        self.on_status = on_status
        self.on_complete = on_complete
        self.on_folder_progress = on_folder_progress  # (current_file, total_files, file_name, file_progress, overall_progress)
        self.hostname = get_hostname()
        self.platform = get_platform()
        self._cancel_folder_transfer = False

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
                    "platform": self.platform,
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
                    "platform": self.platform,
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

    def _calculate_file_hash(self, filepath: str) -> str:
        """計算檔案的 MD5 hash"""
        hash_md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(FILE_CHUNK_SIZE), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _get_folder_files(self, folder_path: str) -> list:
        """取得資料夾內所有檔案的資訊"""
        files = []
        folder_name = os.path.basename(folder_path)

        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                # 計算相對路徑（相對於資料夾根目錄）
                rel_path = os.path.relpath(filepath, folder_path)
                filesize = os.path.getsize(filepath)

                files.append({
                    'filepath': filepath,
                    'rel_path': rel_path,
                    'size': filesize
                })

        return files

    def _recv_response(self, sock: socket.socket) -> str:
        """接收回應"""
        try:
            response = sock.recv(BUFFER_SIZE).decode('utf-8')
            return response
        except:
            return ""

    def cancel_folder_transfer(self):
        """取消資料夾傳輸"""
        self._cancel_folder_transfer = True

    def send_folder(self, target_ip: str, folder_path: str, resume_state: dict = None) -> bool:
        """
        發送資料夾（支援斷點續傳）

        resume_state: 續傳狀態，包含已完成的檔案列表
        """
        if not os.path.isdir(folder_path):
            self._log(f"資料夾不存在: {folder_path}")
            if self.on_complete:
                self.on_complete(False, "資料夾不存在")
            return False

        self._cancel_folder_transfer = False

        def _send():
            sock = None
            try:
                # 取得所有檔案資訊
                files = self._get_folder_files(folder_path)
                if not files:
                    self._log("資料夾是空的")
                    if self.on_complete:
                        self.on_complete(False, "資料夾是空的")
                    return False

                folder_name = os.path.basename(folder_path)
                total_files = len(files)
                total_size = sum(f['size'] for f in files)

                # 已完成的檔案（用於續傳）
                completed_files = set()
                if resume_state and 'completed' in resume_state:
                    completed_files = set(resume_state['completed'])

                # 建立連接
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(60)
                sock.connect((target_ip, TRANSFER_PORT))

                # 發送 FOLDER_START
                header = {
                    "type": MSG_TYPE_FOLDER_START,
                    "sender": self.hostname,
                    "platform": self.platform,
                    "folder_name": folder_name,
                    "total_files": total_files,
                    "total_size": total_size
                }
                header_json = json.dumps(header).encode('utf-8')
                sock.send(len(header_json).to_bytes(4, 'big'))
                sock.send(header_json)

                # 等待 ACK
                response = self._recv_response(sock)
                if response != RESP_ACK:
                    raise Exception(f"FOLDER_START 未收到確認: {response}")

                self._log(f"開始發送資料夾: {folder_name} ({total_files} 檔案, {total_size} bytes)")

                # 逐一發送檔案
                sent_size = 0
                for idx, file_info in enumerate(files):
                    if self._cancel_folder_transfer:
                        raise Exception("傳輸已取消")

                    filepath = file_info['filepath']
                    rel_path = file_info['rel_path']
                    filesize = file_info['size']

                    # 檢查是否已完成（續傳）
                    if rel_path in completed_files:
                        sent_size += filesize
                        continue

                    # 計算檔案 hash
                    file_hash = self._calculate_file_hash(filepath)

                    # 發送 FOLDER_FILE 標頭
                    file_header = {
                        "type": MSG_TYPE_FOLDER_FILE,
                        "rel_path": rel_path,
                        "size": filesize,
                        "hash": file_hash,
                        "index": idx + 1,
                        "total": total_files
                    }
                    file_header_json = json.dumps(file_header).encode('utf-8')
                    sock.send(len(file_header_json).to_bytes(4, 'big'))
                    sock.send(file_header_json)

                    # 等待回應（ACK 或 SKIP）
                    response = self._recv_response(sock)

                    if response == RESP_SKIP:
                        # 檔案已存在且 hash 相同，跳過
                        self._log(f"跳過 (已存在): {rel_path}")
                        sent_size += filesize
                        completed_files.add(rel_path)

                        # 更新進度
                        overall_progress = (sent_size / total_size) * 100 if total_size > 0 else 100
                        if self.on_folder_progress:
                            self.on_folder_progress(idx + 1, total_files, rel_path, 100, overall_progress, "skipped")
                        continue

                    if response != RESP_ACK:
                        raise Exception(f"檔案 {rel_path} 未收到確認: {response}")

                    # 發送檔案內容
                    file_sent = 0
                    with open(filepath, 'rb') as f:
                        while file_sent < filesize:
                            if self._cancel_folder_transfer:
                                raise Exception("傳輸已取消")

                            chunk = f.read(FILE_CHUNK_SIZE)
                            if not chunk:
                                break
                            sock.send(chunk)
                            file_sent += len(chunk)

                            # 更新進度
                            file_progress = (file_sent / filesize) * 100 if filesize > 0 else 100
                            overall_progress = ((sent_size + file_sent) / total_size) * 100 if total_size > 0 else 100

                            if self.on_folder_progress:
                                self.on_folder_progress(idx + 1, total_files, rel_path, file_progress, overall_progress, "sending")

                            if self.on_progress:
                                self.on_progress(overall_progress, f"({idx + 1}/{total_files}) {rel_path}")

                    # 等待檔案傳輸確認
                    response = self._recv_response(sock)
                    if response != RESP_ACK:
                        raise Exception(f"檔案 {rel_path} 傳輸確認失敗: {response}")

                    sent_size += filesize
                    completed_files.add(rel_path)

                    # 更新進度為完成
                    overall_progress = (sent_size / total_size) * 100 if total_size > 0 else 100
                    if self.on_folder_progress:
                        self.on_folder_progress(idx + 1, total_files, rel_path, 100, overall_progress, "completed")

                # 發送 FOLDER_END
                end_header = {
                    "type": MSG_TYPE_FOLDER_END,
                    "folder_name": folder_name,
                    "total_sent": len(completed_files)
                }
                end_header_json = json.dumps(end_header).encode('utf-8')
                sock.send(len(end_header_json).to_bytes(4, 'big'))
                sock.send(end_header_json)

                # 等待最終確認
                response = self._recv_response(sock)
                sock.close()

                if response == RESP_ACK:
                    self._log(f"資料夾傳輸完成: {folder_name}")
                    if self.on_complete:
                        self.on_complete(True, f"資料夾 {folder_name} 發送成功 ({total_files} 檔案)")
                    return True
                else:
                    raise Exception(f"FOLDER_END 未收到確認: {response}")

            except Exception as e:
                self._log(f"發送資料夾失敗: {e}")
                if self.on_complete:
                    self.on_complete(False, str(e))
                return False
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass

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
