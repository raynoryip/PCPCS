"""
TCP 傳輸客戶端
負責發送文字和檔案到其他節點
"""
import socket
import json
import os
import threading
import time
from typing import Callable, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    TRANSFER_PORT, BUFFER_SIZE, FILE_CHUNK_SIZE,
    MSG_TYPE_TEXT, MSG_TYPE_FILE,
    MSG_TYPE_FOLDER_START, MSG_TYPE_FOLDER_FILE, MSG_TYPE_FOLDER_END,
    MSG_TYPE_PARALLEL_FILE, MSG_TYPE_PARALLEL_CHUNK, MSG_TYPE_PARALLEL_DONE,
    RESP_ACK_STRIPPED, RESP_SKIP_STRIPPED, RESP_LENGTH,
    SOCKET_SEND_BUFFER, SOCKET_RECV_BUFFER,
    PARALLEL_CONNECTIONS, PARALLEL_CHUNK_SIZE, PARALLEL_PORT_START, PARALLEL_MIN_FILE_SIZE,
    get_hostname, get_platform
)

# 高速發送塊大小 (256KB - 減少系統調用次數)
SEND_CHUNK_SIZE = 262144
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# 檢查是否支援 sendfile (Linux/macOS)
try:
    _sendfile = os.sendfile
    HAS_SENDFILE = True
except AttributeError:
    HAS_SENDFILE = False


def optimize_socket(sock: socket.socket):
    """優化 socket 設定以獲得最大傳輸速度"""
    # 增大緩衝區
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKET_SEND_BUFFER)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_RECV_BUFFER)
    # 禁用 Nagle 演算法 (減少延遲)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


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

    def _format_time(self, seconds: float) -> str:
        """格式化剩餘時間"""
        if seconds < 0 or seconds > 86400:  # > 24 hours
            return "--:--"
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"

    def _send_file_data(self, sock: socket.socket, filepath: str, filesize: int,
                        on_progress_callback: Optional[Callable] = None) -> int:
        """
        高效發送檔案數據 (使用 sendfile 或 fallback)
        返回實際發送的字節數
        """
        sent = 0
        start_time = time.time()

        if HAS_SENDFILE:
            # 使用 zero-copy sendfile (Linux/macOS)
            with open(filepath, 'rb') as f:
                fd = f.fileno()
                sock_fd = sock.fileno()
                while sent < filesize:
                    try:
                        # sendfile 一次最多傳輸 2GB
                        chunk_to_send = min(filesize - sent, 0x7FFFFFFF)
                        n = _sendfile(sock_fd, fd, sent, chunk_to_send)
                        if n == 0:
                            break
                        sent += n

                        # 更新進度
                        if on_progress_callback:
                            elapsed = time.time() - start_time
                            speed = sent / elapsed if elapsed > 0 else 0
                            remaining = (filesize - sent) / speed if speed > 0 else 0
                            on_progress_callback(sent, filesize, speed, remaining)
                    except BlockingIOError:
                        continue
        else:
            # Fallback: 普通 read/send
            with open(filepath, 'rb') as f:
                while sent < filesize:
                    chunk = f.read(FILE_CHUNK_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk)
                    sent += len(chunk)

                    # 更新進度
                    if on_progress_callback:
                        elapsed = time.time() - start_time
                        speed = sent / elapsed if elapsed > 0 else 0
                        remaining = (filesize - sent) / speed if speed > 0 else 0
                        on_progress_callback(sent, filesize, speed, remaining)

        return sent

    def send_text(self, target_ip: str, text: str) -> bool:
        """
        發送文字訊息
        """
        def _send():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                optimize_socket(sock)
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

    def _send_chunk_worker(self, target_ip: str, port: int, filepath: str,
                           chunk_id: int, start_offset: int, chunk_size: int,
                           progress_dict: dict, lock: threading.Lock) -> bool:
        """
        並行傳輸的單個分塊工作者
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            optimize_socket(sock)
            sock.settimeout(300)
            sock.connect((target_ip, port))

            # 發送分塊標頭
            header = {
                "type": MSG_TYPE_PARALLEL_CHUNK,
                "chunk_id": chunk_id,
                "offset": start_offset,
                "size": chunk_size
            }
            header_json = json.dumps(header).encode('utf-8')
            sock.send(len(header_json).to_bytes(4, 'big'))
            sock.send(header_json)

            # 等待 ACK
            response = self._recv_response(sock)
            if response != RESP_ACK_STRIPPED:
                sock.close()
                return False

            # 發送分塊數據 (使用較大的塊減少系統調用)
            sent = 0
            with open(filepath, 'rb') as f:
                f.seek(start_offset)
                while sent < chunk_size:
                    read_size = min(SEND_CHUNK_SIZE, chunk_size - sent)
                    data = f.read(read_size)
                    if not data:
                        break
                    sock.sendall(data)
                    sent += len(data)

                    # 更新進度
                    with lock:
                        progress_dict[chunk_id] = sent

            # 等待確認
            response = self._recv_response(sock)
            sock.close()
            return response == RESP_ACK_STRIPPED

        except Exception as e:
            self._log(f"分塊 {chunk_id} 傳輸失敗: {e}")
            return False

    def send_file_parallel(self, target_ip: str, filepath: str) -> bool:
        """
        使用多連接並行發送大檔案 (類似 FileZilla)
        """
        if not os.path.exists(filepath):
            self._log(f"檔案不存在: {filepath}")
            if self.on_complete:
                self.on_complete(False, "檔案不存在")
            return False

        def _send_parallel():
            try:
                filesize = os.path.getsize(filepath)
                filename = os.path.basename(filepath)

                # 建立主控制連接
                main_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                optimize_socket(main_sock)
                main_sock.settimeout(30)
                main_sock.connect((target_ip, TRANSFER_PORT))

                # 計算分塊
                num_chunks = min(PARALLEL_CONNECTIONS, max(1, filesize // PARALLEL_CHUNK_SIZE))
                chunk_size = filesize // num_chunks
                chunks = []

                for i in range(num_chunks):
                    start = i * chunk_size
                    if i == num_chunks - 1:
                        # 最後一塊包含剩餘所有字節
                        size = filesize - start
                    else:
                        size = chunk_size
                    chunks.append({
                        "chunk_id": i,
                        "offset": start,
                        "size": size,
                        "port": PARALLEL_PORT_START + i
                    })

                # 發送並行傳輸請求
                header = {
                    "type": MSG_TYPE_PARALLEL_FILE,
                    "sender": self.hostname,
                    "platform": self.platform,
                    "filename": filename,
                    "filesize": filesize,
                    "num_chunks": num_chunks,
                    "chunks": chunks
                }
                header_json = json.dumps(header).encode('utf-8')
                main_sock.send(len(header_json).to_bytes(4, 'big'))
                main_sock.send(header_json)

                # 等待伺服器準備好接收
                response = self._recv_response(main_sock)
                if response != RESP_ACK_STRIPPED:
                    raise Exception(f"伺服器未準備好: {response}")

                self._log(f"開始並行發送檔案: {filename} ({filesize} bytes, {num_chunks} 連接)")

                # 進度追蹤
                progress_dict = {i: 0 for i in range(num_chunks)}
                lock = threading.Lock()
                start_time = time.time()

                # 啟動進度更新線程
                progress_running = True
                def update_progress():
                    while progress_running:
                        with lock:
                            total_sent = sum(progress_dict.values())
                        progress = (total_sent / filesize) * 100
                        elapsed = time.time() - start_time
                        speed = total_sent / elapsed if elapsed > 0 else 0
                        remaining = (filesize - total_sent) / speed if speed > 0 else 0
                        speed_mb = speed / (1024 * 1024)
                        time_str = self._format_time(remaining)

                        if self.on_progress:
                            self.on_progress(progress, f"{filename} ({speed_mb:.1f} MB/s, {time_str})")
                        time.sleep(0.1)

                progress_thread = threading.Thread(target=update_progress, daemon=True)
                progress_thread.start()

                # 並行發送所有分塊
                with ThreadPoolExecutor(max_workers=num_chunks) as executor:
                    futures = []
                    for chunk in chunks:
                        future = executor.submit(
                            self._send_chunk_worker,
                            target_ip,
                            chunk["port"],
                            filepath,
                            chunk["chunk_id"],
                            chunk["offset"],
                            chunk["size"],
                            progress_dict,
                            lock
                        )
                        futures.append(future)

                    # 等待所有分塊完成
                    results = [f.result() for f in as_completed(futures)]

                progress_running = False

                if not all(results):
                    raise Exception("部分分塊傳輸失敗")

                # 發送完成信號
                done_header = {
                    "type": MSG_TYPE_PARALLEL_DONE,
                    "filename": filename,
                    "filesize": filesize
                }
                done_json = json.dumps(done_header).encode('utf-8')
                main_sock.send(len(done_json).to_bytes(4, 'big'))
                main_sock.send(done_json)

                # 等待最終確認
                response = self._recv_response(main_sock)
                main_sock.close()

                elapsed = time.time() - start_time
                avg_speed = filesize / elapsed if elapsed > 0 else 0
                avg_speed_mb = avg_speed / (1024 * 1024)

                if response == RESP_ACK_STRIPPED:
                    self._log(f"檔案已發送到 {target_ip} (平均 {avg_speed_mb:.1f} MB/s)")
                    if self.on_complete:
                        self.on_complete(True, f"檔案 {filename} 發送成功 ({avg_speed_mb:.1f} MB/s)")
                    return True
                else:
                    raise Exception(f"傳輸確認失敗: {response}")

            except Exception as e:
                self._log(f"並行發送檔案失敗: {e}")
                if self.on_complete:
                    self.on_complete(False, str(e))
                return False

        thread = threading.Thread(target=_send_parallel, daemon=True)
        thread.start()
        return True

    def send_file(self, target_ip: str, filepath: str) -> bool:
        """
        發送檔案 (大檔案自動使用並行傳輸)
        """
        if not os.path.exists(filepath):
            self._log(f"檔案不存在: {filepath}")
            if self.on_complete:
                self.on_complete(False, "檔案不存在")
            return False

        # 大檔案使用並行傳輸
        filesize = os.path.getsize(filepath)
        if filesize >= PARALLEL_MIN_FILE_SIZE:
            return self.send_file_parallel(target_ip, filepath)

        def _send():
            try:
                filesize = os.path.getsize(filepath)
                filename = os.path.basename(filepath)

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                optimize_socket(sock)
                sock.settimeout(300)  # 5 分鐘超時 (大檔案)
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

                # 進度回調
                def progress_callback(sent, total, speed, remaining):
                    if self.on_progress:
                        progress = (sent / total) * 100
                        speed_mb = speed / (1024 * 1024)
                        time_str = self._format_time(remaining)
                        self.on_progress(progress, f"{filename} ({speed_mb:.1f} MB/s, {time_str})")

                # 使用高效發送
                self._send_file_data(sock, filepath, filesize, progress_callback)

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

    def _calculate_file_hash(self, filepath: str, quick: bool = True) -> str:
        """
        計算檔案的 hash
        quick=True: 只讀取檔案頭尾各 64KB + 檔案大小，速度快但不完全精確
        quick=False: 完整 MD5 hash，精確但慢
        """
        filesize = os.path.getsize(filepath)

        if quick:
            # 快速 hash：檔案大小 + 頭尾各 64KB
            hash_data = str(filesize).encode()
            with open(filepath, 'rb') as f:
                # 讀取頭部
                hash_data += f.read(65536)
                # 讀取尾部
                if filesize > 65536:
                    f.seek(-65536, 2)
                    hash_data += f.read(65536)
            return hashlib.md5(hash_data).hexdigest()
        else:
            # 完整 MD5
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

    def _recv_exact(self, sock: socket.socket, size: int) -> Optional[bytes]:
        """精確接收指定大小的數據"""
        data = b''
        while len(data) < size:
            chunk = sock.recv(min(size - len(data), BUFFER_SIZE))
            if not chunk:
                return None
            data += chunk
        return data

    def _recv_response(self, sock: socket.socket) -> str:
        """接收固定長度回應 (避免 TCP 黏包)"""
        try:
            data = self._recv_exact(sock, RESP_LENGTH)
            if data:
                return data.decode('utf-8').rstrip('_')  # 去除填充字元
            return ""
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
                optimize_socket(sock)
                sock.settimeout(300)  # 5 分鐘超時
                sock.connect((target_ip, TRANSFER_PORT))

                # 傳輸時間追蹤
                transfer_start_time = time.time()

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
                if response != RESP_ACK_STRIPPED:
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

                    if response == RESP_SKIP_STRIPPED:
                        # 檔案已存在且 hash 相同，跳過
                        self._log(f"跳過 (已存在): {rel_path}")
                        sent_size += filesize
                        completed_files.add(rel_path)

                        # 更新進度
                        overall_progress = (sent_size / total_size) * 100 if total_size > 0 else 100
                        if self.on_folder_progress:
                            self.on_folder_progress(idx + 1, total_files, rel_path, 100, overall_progress, "skipped")
                        continue

                    if response != RESP_ACK_STRIPPED:
                        raise Exception(f"檔案 {rel_path} 未收到確認: {response}")

                    # 發送檔案內容 (使用高效發送或 fallback)
                    file_sent = 0
                    file_start_time = time.time()

                    if HAS_SENDFILE and filesize > 0:
                        # 使用 zero-copy sendfile
                        with open(filepath, 'rb') as f:
                            fd = f.fileno()
                            sock_fd = sock.fileno()
                            while file_sent < filesize:
                                if self._cancel_folder_transfer:
                                    raise Exception("傳輸已取消")
                                try:
                                    chunk_to_send = min(filesize - file_sent, 0x7FFFFFFF)
                                    n = _sendfile(sock_fd, fd, file_sent, chunk_to_send)
                                    if n == 0:
                                        break
                                    file_sent += n

                                    # 更新進度
                                    file_progress = (file_sent / filesize) * 100
                                    overall_progress = ((sent_size + file_sent) / total_size) * 100 if total_size > 0 else 100

                                    # 計算速度和剩餘時間
                                    elapsed = time.time() - transfer_start_time
                                    total_sent_now = sent_size + file_sent
                                    speed = total_sent_now / elapsed if elapsed > 0 else 0
                                    remaining_bytes = total_size - total_sent_now
                                    remaining_time = remaining_bytes / speed if speed > 0 else 0
                                    speed_mb = speed / (1024 * 1024)
                                    time_str = self._format_time(remaining_time)

                                    if self.on_folder_progress:
                                        self.on_folder_progress(idx + 1, total_files, rel_path, file_progress, overall_progress, "sending")

                                    if self.on_progress:
                                        self.on_progress(overall_progress, f"({idx + 1}/{total_files}) {rel_path} ({speed_mb:.1f} MB/s, {time_str})")
                                except BlockingIOError:
                                    continue
                    else:
                        # Fallback: 普通 read/send
                        with open(filepath, 'rb') as f:
                            while file_sent < filesize:
                                if self._cancel_folder_transfer:
                                    raise Exception("傳輸已取消")

                                chunk = f.read(FILE_CHUNK_SIZE)
                                if not chunk:
                                    break
                                sock.sendall(chunk)
                                file_sent += len(chunk)

                                # 更新進度
                                file_progress = (file_sent / filesize) * 100 if filesize > 0 else 100
                                overall_progress = ((sent_size + file_sent) / total_size) * 100 if total_size > 0 else 100

                                # 計算速度和剩餘時間
                                elapsed = time.time() - transfer_start_time
                                total_sent_now = sent_size + file_sent
                                speed = total_sent_now / elapsed if elapsed > 0 else 0
                                remaining_bytes = total_size - total_sent_now
                                remaining_time = remaining_bytes / speed if speed > 0 else 0
                                speed_mb = speed / (1024 * 1024)
                                time_str = self._format_time(remaining_time)

                                if self.on_folder_progress:
                                    self.on_folder_progress(idx + 1, total_files, rel_path, file_progress, overall_progress, "sending")

                                if self.on_progress:
                                    self.on_progress(overall_progress, f"({idx + 1}/{total_files}) {rel_path} ({speed_mb:.1f} MB/s, {time_str})")

                    # 等待檔案傳輸確認
                    response = self._recv_response(sock)
                    if response != RESP_ACK_STRIPPED:
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

                if response == RESP_ACK_STRIPPED:
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
