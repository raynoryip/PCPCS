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
    MSG_TYPE_TEXT, MSG_TYPE_FILE, MSG_TYPE_FILE_CHUNK, MSG_TYPE_FILE_END,
    MSG_TYPE_FOLDER_START, MSG_TYPE_FOLDER_FILE, MSG_TYPE_FOLDER_END,
    MSG_TYPE_PARALLEL_FILE, MSG_TYPE_PARALLEL_CHUNK, MSG_TYPE_PARALLEL_DONE,
    RESP_ACK, RESP_SKIP, RESP_ERROR, RESP_LENGTH,
    SOCKET_SEND_BUFFER, SOCKET_RECV_BUFFER,
    PARALLEL_CONNECTIONS, PARALLEL_PORT_START
)

# 高速接收緩衝區大小 (256KB - 減少系統調用次數)
RECV_CHUNK_SIZE = 262144
from concurrent.futures import ThreadPoolExecutor
import hashlib


def optimize_socket(sock: socket.socket):
    """優化 socket 設定以獲得最大傳輸速度"""
    # 增大緩衝區
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKET_SEND_BUFFER)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_RECV_BUFFER)
    # 禁用 Nagle 演算法 (減少延遲)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


class TransferServer:
    """傳輸接收伺服器"""

    def __init__(self,
                 on_text_received: Optional[Callable] = None,
                 on_file_received: Optional[Callable] = None,
                 on_folder_received: Optional[Callable] = None,
                 on_progress: Optional[Callable] = None,
                 on_folder_progress: Optional[Callable] = None,
                 on_status: Optional[Callable] = None,
                 on_transfer_start: Optional[Callable] = None):
        self.on_text_received = on_text_received
        self.on_file_received = on_file_received
        self.on_folder_received = on_folder_received  # (sender_ip, sender_name, folder_path, total_files, total_size)
        self.on_progress = on_progress
        self.on_folder_progress = on_folder_progress  # (current_file, total_files, file_name, file_progress, overall_progress, status)
        self.on_status = on_status
        self.on_transfer_start = on_transfer_start  # (total_size) - 通知 GUI 開始接收

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
                    optimize_socket(client_socket)  # 優化接收端 socket
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
                client_socket.send(b"OK")
            elif msg_type == MSG_TYPE_FILE:
                self._handle_file(client_socket, header, client_ip)
                client_socket.send(b"OK")
            elif msg_type == MSG_TYPE_PARALLEL_FILE:
                self._handle_parallel_file(client_socket, header, client_ip)
                # parallel handler sends its own responses
            elif msg_type == MSG_TYPE_FOLDER_START:
                self._handle_folder(client_socket, header, client_ip)
                # folder handler sends its own responses

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

        # 通知 GUI 開始接收（用於 ETA 計算）
        if self.on_transfer_start:
            self.on_transfer_start(filesize)

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

    def _recv_response_stripped(self, sock: socket.socket) -> str:
        """接收固定長度回應並去除填充"""
        try:
            data = self._recv_exact(sock, RESP_LENGTH)
            if data:
                return data.decode('utf-8').rstrip('_')
            return ""
        except:
            return ""

    def _handle_parallel_chunk_worker(self, port: int, filepath: str,
                                      chunk_info: dict, progress_dict: dict,
                                      lock: threading.Lock) -> bool:
        """
        處理單個並行分塊的接收 (優化版 - 使用 recv_into 零拷貝)
        """
        chunk_id = chunk_info["chunk_id"]
        expected_offset = chunk_info["offset"]
        expected_size = chunk_info["size"]

        try:
            # 創建監聽 socket
            chunk_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            chunk_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            optimize_socket(chunk_sock)
            chunk_sock.bind(('', port))
            chunk_sock.listen(1)
            chunk_sock.settimeout(30)

            # 等待連接
            conn, addr = chunk_sock.accept()
            optimize_socket(conn)
            conn.settimeout(300)

            # 接收分塊標頭
            header_len_data = self._recv_exact(conn, 4)
            if not header_len_data:
                raise Exception("未收到標頭")

            header_length = int.from_bytes(header_len_data, 'big')
            header_json = self._recv_exact(conn, header_length)
            header = json.loads(header_json.decode('utf-8'))

            if header.get("type") != MSG_TYPE_PARALLEL_CHUNK:
                raise Exception(f"錯誤的訊息類型: {header.get('type')}")

            if header.get("chunk_id") != chunk_id:
                raise Exception(f"分塊 ID 不匹配: {header.get('chunk_id')} != {chunk_id}")

            # 發送 ACK
            conn.send(RESP_ACK.encode('utf-8'))

            # 使用 recv_into 零拷貝接收 - 直接寫入預分配的緩衝區
            received = 0
            # 使用較大的緩衝區減少系統調用次數
            buf = bytearray(RECV_CHUNK_SIZE)
            view = memoryview(buf)

            with open(filepath, 'r+b') as f:
                f.seek(expected_offset)
                while received < expected_size:
                    # 計算這次要接收的大小
                    to_recv = min(RECV_CHUNK_SIZE, expected_size - received)
                    # 使用 recv_into 直接寫入緩衝區，避免記憶體分配
                    bytes_read = conn.recv_into(view[:to_recv])
                    if bytes_read == 0:
                        raise Exception("連接中斷")
                    # 直接寫入檔案
                    f.write(view[:bytes_read])
                    received += bytes_read

                    with lock:
                        progress_dict[chunk_id] = received

            # 發送完成確認
            conn.send(RESP_ACK.encode('utf-8'))
            conn.close()
            chunk_sock.close()
            return True

        except Exception as e:
            self._log(f"分塊 {chunk_id} 接收失敗: {e}")
            return False

    def _handle_parallel_file(self, sock: socket.socket, header: dict, sender_ip: str):
        """處理並行檔案傳輸"""
        filename = header.get("filename", "unknown_file")
        filesize = header.get("filesize", 0)
        num_chunks = header.get("num_chunks", 1)
        chunks = header.get("chunks", [])
        sender_name = header.get("sender", sender_ip)
        sender_platform = header.get("platform", "Unknown")

        # 安全處理檔名
        safe_filename = os.path.basename(filename)
        filepath = os.path.join(RECEIVE_DIR, safe_filename)

        # 如果檔案已存在，添加編號
        base, ext = os.path.splitext(safe_filename)
        counter = 1
        while os.path.exists(filepath):
            filepath = os.path.join(RECEIVE_DIR, f"{base}_{counter}{ext}")
            counter += 1

        self._log(f"開始並行接收檔案: {safe_filename} ({filesize} bytes, {num_chunks} 連接)")

        # 通知 GUI 開始接收（用於 ETA 計算）
        if self.on_transfer_start:
            self.on_transfer_start(filesize)

        try:
            # 預先創建檔案並分配空間
            with open(filepath, 'wb') as f:
                f.seek(filesize - 1)
                f.write(b'\0')

            # 發送準備好信號
            sock.send(RESP_ACK.encode('utf-8'))

            # 進度追蹤
            progress_dict = {i: 0 for i in range(num_chunks)}
            lock = threading.Lock()

            # 啟動並行接收工作者
            with ThreadPoolExecutor(max_workers=num_chunks) as executor:
                futures = []
                for chunk in chunks:
                    future = executor.submit(
                        self._handle_parallel_chunk_worker,
                        chunk["port"],
                        filepath,
                        chunk,
                        progress_dict,
                        lock
                    )
                    futures.append(future)

                # 等待所有分塊完成，同時更新進度
                while not all(f.done() for f in futures):
                    with lock:
                        total_received = sum(progress_dict.values())
                    if self.on_progress:
                        progress = (total_received / filesize) * 100
                        self.on_progress(progress, f"接收中: {safe_filename}")
                    import time
                    time.sleep(0.1)

                results = [f.result() for f in futures]

            if not all(results):
                raise Exception("部分分塊接收失敗")

            # 等待完成信號
            header_len_data = self._recv_exact(sock, 4)
            if not header_len_data:
                raise Exception("未收到完成信號")

            header_length = int.from_bytes(header_len_data, 'big')
            done_json = self._recv_exact(sock, header_length)
            done_header = json.loads(done_json.decode('utf-8'))

            if done_header.get("type") != MSG_TYPE_PARALLEL_DONE:
                raise Exception(f"錯誤的完成信號: {done_header.get('type')}")

            # 發送最終確認
            sock.send(RESP_ACK.encode('utf-8'))

            self._log(f"檔案並行接收完成: {filepath}")

            if self.on_file_received:
                self.on_file_received(sender_ip, sender_name, filepath, filesize, sender_platform)

        except Exception as e:
            self._log(f"並行檔案接收失敗: {e}")
            sock.send(RESP_ERROR.encode('utf-8'))
            # 刪除不完整的檔案
            if os.path.exists(filepath):
                os.remove(filepath)

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

    def _handle_folder(self, sock: socket.socket, header: dict, sender_ip: str):
        """處理資料夾傳輸"""
        folder_name = header.get("folder_name", "unknown_folder")
        total_files = header.get("total_files", 0)
        total_size = header.get("total_size", 0)
        sender_name = header.get("sender", sender_ip)
        sender_platform = header.get("platform", "Unknown")

        # 安全處理資料夾名稱
        safe_folder_name = os.path.basename(folder_name)

        # 建立接收資料夾
        folder_path = os.path.join(RECEIVE_DIR, safe_folder_name)

        # 如果資料夾已存在，添加編號
        base_folder = folder_path
        counter = 1
        while os.path.exists(folder_path):
            folder_path = f"{base_folder}_{counter}"
            counter += 1

        os.makedirs(folder_path, exist_ok=True)

        self._log(f"開始接收資料夾: {safe_folder_name} ({total_files} 檔案, {total_size} bytes)")

        # 通知 GUI 開始接收（用於 ETA 計算）
        if self.on_transfer_start:
            self.on_transfer_start(total_size)

        # 發送 ACK
        sock.send(RESP_ACK.encode('utf-8'))

        received_size = 0
        received_files = 0

        try:
            while True:
                # 接收下一個標頭
                header_len_data = self._recv_exact(sock, 4)
                if not header_len_data:
                    raise Exception("連接中斷")

                header_length = int.from_bytes(header_len_data, 'big')
                header_json = self._recv_exact(sock, header_length)
                if not header_json:
                    raise Exception("連接中斷")

                file_header = json.loads(header_json.decode('utf-8'))
                msg_type = file_header.get("type")

                if msg_type == MSG_TYPE_FOLDER_END:
                    # 資料夾傳輸完成
                    sock.send(RESP_ACK.encode('utf-8'))
                    self._log(f"資料夾接收完成: {folder_path}")

                    if self.on_folder_received:
                        self.on_folder_received(sender_ip, sender_name, folder_path, received_files, received_size, sender_platform)
                    break

                elif msg_type == MSG_TYPE_FOLDER_FILE:
                    # 接收單個檔案
                    rel_path = file_header.get("rel_path", "unknown_file")
                    filesize = file_header.get("size", 0)
                    file_hash = file_header.get("hash", "")
                    file_index = file_header.get("index", 0)
                    file_total = file_header.get("total", total_files)

                    # 安全處理相對路徑
                    # 防止路徑穿越攻擊
                    safe_rel_path = os.path.normpath(rel_path)
                    if safe_rel_path.startswith('..') or os.path.isabs(safe_rel_path):
                        safe_rel_path = os.path.basename(rel_path)

                    filepath = os.path.join(folder_path, safe_rel_path)

                    # 確保子目錄存在
                    file_dir = os.path.dirname(filepath)
                    if file_dir and not os.path.exists(file_dir):
                        os.makedirs(file_dir, exist_ok=True)

                    # 檢查檔案是否已存在且 hash 相同（用於續傳）
                    if os.path.exists(filepath) and file_hash:
                        existing_hash = self._calculate_file_hash(filepath)
                        if existing_hash == file_hash:
                            # 檔案已存在且相同，跳過
                            sock.send(RESP_SKIP.encode('utf-8'))
                            received_size += filesize
                            received_files += 1

                            overall_progress = (received_size / total_size) * 100 if total_size > 0 else 100
                            if self.on_folder_progress:
                                self.on_folder_progress(file_index, file_total, safe_rel_path, 100, overall_progress, "skipped")

                            self._log(f"跳過 (已存在): {safe_rel_path}")
                            continue

                    # 發送 ACK，準備接收檔案
                    sock.send(RESP_ACK.encode('utf-8'))

                    # 接收檔案內容
                    file_received = 0
                    try:
                        with open(filepath, 'wb') as f:
                            while file_received < filesize:
                                chunk_size = min(FILE_CHUNK_SIZE, filesize - file_received)
                                chunk = self._recv_exact(sock, chunk_size)
                                if not chunk:
                                    raise Exception("連接中斷")

                                f.write(chunk)
                                file_received += len(chunk)

                                # 更新進度
                                file_progress = (file_received / filesize) * 100 if filesize > 0 else 100
                                overall_progress = ((received_size + file_received) / total_size) * 100 if total_size > 0 else 100

                                if self.on_folder_progress:
                                    self.on_folder_progress(file_index, file_total, safe_rel_path, file_progress, overall_progress, "receiving")

                                if self.on_progress:
                                    self.on_progress(overall_progress, f"({file_index}/{file_total}) {safe_rel_path}")

                        # 驗證 hash
                        if file_hash:
                            received_hash = self._calculate_file_hash(filepath)
                            if received_hash != file_hash:
                                os.remove(filepath)
                                raise Exception(f"檔案 {safe_rel_path} hash 驗證失敗")

                        # 發送檔案接收確認
                        sock.send(RESP_ACK.encode('utf-8'))

                        received_size += filesize
                        received_files += 1

                        overall_progress = (received_size / total_size) * 100 if total_size > 0 else 100
                        if self.on_folder_progress:
                            self.on_folder_progress(file_index, file_total, safe_rel_path, 100, overall_progress, "completed")

                        self._log(f"接收完成 ({file_index}/{file_total}): {safe_rel_path}")

                    except Exception as e:
                        # 刪除不完整的檔案
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        raise e

                else:
                    # 未知訊息類型
                    self._log(f"未知訊息類型: {msg_type}")
                    sock.send(RESP_ERROR.encode('utf-8'))

        except Exception as e:
            self._log(f"資料夾接收失敗: {e}")
            sock.send(RESP_ERROR.encode('utf-8'))


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
