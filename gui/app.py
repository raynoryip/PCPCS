"""
PCPCS GUI 介面
使用 Tkinter 實作跨平台圖形介面
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import get_hostname, get_local_ip, RECEIVE_DIR
from network.discovery import NetworkDiscovery, PeerInfo
from network.server import TransferServer
from network.client import TransferClient


class PCPCSApp:
    """PCPCS 主應用程式"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"PCPCS - {get_hostname()} ({get_local_ip()})")
        self.root.geometry("900x650")
        self.root.minsize(800, 550)

        # 設定樣式
        self.style = ttk.Style()
        self._setup_styles()

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

        # 選中的目標
        self.selected_peer_ip = None

        # 建立 UI
        self._create_ui()

        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        """設定 UI 樣式"""
        self.style.configure('Title.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('Status.TLabel', font=('Helvetica', 9))
        self.style.configure('Peer.TFrame', relief='raised', borderwidth=1)

    def _create_ui(self):
        """建立使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側 - 節點列表
        left_frame = ttk.LabelFrame(main_frame, text="已發現的電腦", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        # 節點列表
        self.peer_listbox = tk.Listbox(left_frame, width=35, height=15, font=('Consolas', 10))
        self.peer_listbox.pack(fill=tk.BOTH, expand=True)
        self.peer_listbox.bind('<<ListboxSelect>>', self._on_peer_select)

        # 重新掃描按鈕
        refresh_btn = ttk.Button(left_frame, text="重新掃描", command=self._refresh_peers)
        refresh_btn.pack(fill=tk.X, pady=(5, 0))

        # 手動 Ping 按鈕
        ping_btn = ttk.Button(left_frame, text="測試連接 (Ping)", command=self._manual_ping)
        ping_btn.pack(fill=tk.X, pady=(5, 0))

        # 手動添加 IP
        add_ip_btn = ttk.Button(left_frame, text="手動添加 IP", command=self._manual_add_ip)
        add_ip_btn.pack(fill=tk.X, pady=(5, 0))

        # 本機資訊
        info_frame = ttk.Frame(left_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(info_frame, text=f"本機: {get_hostname()}", style='Status.TLabel').pack(anchor='w')
        ttk.Label(info_frame, text=f"IP: {get_local_ip()}", style='Status.TLabel').pack(anchor='w')

        # 右側框架
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 目標顯示
        target_frame = ttk.Frame(right_frame)
        target_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(target_frame, text="目標電腦:", style='Title.TLabel').pack(side=tk.LEFT)
        self.target_label = ttk.Label(target_frame, text="(請從左側選擇)", style='Status.TLabel')
        self.target_label.pack(side=tk.LEFT, padx=(10, 0))

        # 文字傳輸區
        text_frame = ttk.LabelFrame(right_frame, text="發送文字", padding="5")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.text_input = scrolledtext.ScrolledText(text_frame, height=6, font=('Consolas', 10))
        self.text_input.pack(fill=tk.BOTH, expand=True)

        text_btn_frame = ttk.Frame(text_frame)
        text_btn_frame.pack(fill=tk.X, pady=(5, 0))
        self.send_text_btn = ttk.Button(text_btn_frame, text="發送文字", command=self._send_text)
        self.send_text_btn.pack(side=tk.RIGHT)
        ttk.Button(text_btn_frame, text="清除", command=lambda: self.text_input.delete('1.0', tk.END)).pack(side=tk.RIGHT, padx=(0, 5))

        # 檔案傳輸區
        file_frame = ttk.LabelFrame(right_frame, text="發送檔案", padding="5")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=tk.X)

        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_select_frame, textvariable=self.file_path_var, font=('Consolas', 10))
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(file_select_frame, text="選擇檔案", command=self._browse_file).pack(side=tk.LEFT, padx=(0, 5))
        self.send_file_btn = ttk.Button(file_select_frame, text="發送檔案", command=self._send_file)
        self.send_file_btn.pack(side=tk.LEFT)

        # 進度條
        progress_frame = ttk.Frame(right_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(progress_frame, text="", style='Status.TLabel')
        self.progress_label.pack(anchor='w')

        # 日誌區域
        log_frame = ttk.LabelFrame(right_frame, text="訊息記錄", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=('Consolas', 9), state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 日誌區底部按鈕
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(log_btn_frame, text="清除記錄", command=self._clear_log).pack(side=tk.LEFT)
        ttk.Button(log_btn_frame, text="開啟接收資料夾", command=self._open_receive_folder).pack(side=tk.RIGHT)

    def _on_peer_update(self, peers: dict):
        """節點列表更新回調"""
        # 在主線程中更新 UI
        self.root.after(0, lambda: self._update_peer_list(peers))

    def _update_peer_list(self, peers: dict):
        """更新節點列表"""
        # 記住當前選擇
        current_selection = self.selected_peer_ip

        self.peer_listbox.delete(0, tk.END)

        for ip, peer in peers.items():
            status = "OK" if peer.is_reachable else "X"
            ping_str = f"{peer.ping_ms:.0f}ms" if peer.ping_ms else "---"
            display = f"[{status}] {peer.hostname} ({peer.platform})"
            display += f"\n    {ip} | {ping_str}"
            self.peer_listbox.insert(tk.END, f"{peer.hostname} | {ip} | {peer.platform} | {ping_str} [{status}]")

        # 恢復選擇
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
            # 解析 IP
            parts = item.split('|')
            if len(parts) >= 2:
                self.selected_peer_ip = parts[1].strip()
                hostname = parts[0].strip()
                self.target_label.config(text=f"{hostname} ({self.selected_peer_ip})")
                self._log(f"已選擇目標: {hostname} ({self.selected_peer_ip})")

    def _refresh_peers(self):
        """重新掃描節點"""
        self._log("正在重新掃描網路...")
        # 清空列表觸發重新發現
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
                self._log(f"Ping {self.selected_peer_ip}: 無回應 - 連接失敗")

        threading.Thread(target=do_ping, daemon=True).start()

    def _manual_add_ip(self):
        """手動添加 IP 地址"""
        from tkinter import simpledialog

        ip = simpledialog.askstring(
            "手動添加 IP",
            "請輸入目標電腦的 IP 地址:",
            parent=self.root
        )

        if ip and ip.strip():
            ip = ip.strip()
            self._log(f"正在嘗試連接 {ip}...")

            def try_connect():
                # 先 ping 測試
                ping_result = self.discovery.manual_ping(ip)

                if ping_result:
                    # 添加到 peers
                    from network.discovery import PeerInfo
                    peer = PeerInfo(ip, f"Manual-{ip}", "Unknown")
                    peer.ping_ms = ping_result
                    peer.is_reachable = True
                    self.discovery.peers[ip] = peer

                    self._log(f"成功添加 {ip} (Ping: {ping_result:.1f}ms)")
                    self.root.after(0, lambda: self._update_peer_list(self.discovery.peers))
                else:
                    self._log(f"無法連接到 {ip}")
                    # 仍然添加，讓用戶可以嘗試
                    from network.discovery import PeerInfo
                    peer = PeerInfo(ip, f"Manual-{ip}", "Unknown")
                    peer.is_reachable = False
                    self.discovery.peers[ip] = peer
                    self.root.after(0, lambda: self._update_peer_list(self.discovery.peers))

            threading.Thread(target=try_connect, daemon=True).start()

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

        text = self.text_input.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "請輸入要發送的文字")
            return

        self._log(f"正在發送文字到 {self.selected_peer_ip}...")
        self.send_text_btn.config(state='disabled')
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

        self._log(f"正在發送檔案到 {self.selected_peer_ip}...")
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
        self.progress_label.config(text=message)

    def _on_send_complete(self, success: bool, message: str):
        """發送完成回調"""
        self.root.after(0, lambda: self._handle_send_complete(success, message))

    def _handle_send_complete(self, success: bool, message: str):
        """處理發送完成"""
        self.send_text_btn.config(state='normal')
        self.send_file_btn.config(state='normal')
        self.progress_var.set(100 if success else 0)
        self.progress_label.config(text=message)

        if success:
            self._log(f"發送成功: {message}")
        else:
            self._log(f"發送失敗: {message}")

    def _on_text_received(self, sender_ip: str, sender_name: str, text: str):
        """收到文字回調"""
        self.root.after(0, lambda: self._show_received_text(sender_ip, sender_name, text))

    def _show_received_text(self, sender_ip: str, sender_name: str, text: str):
        """顯示收到的文字"""
        self._log(f"收到來自 {sender_name} ({sender_ip}) 的文字")
        messagebox.showinfo(
            f"收到文字 - 來自 {sender_name}",
            text[:500] + ("..." if len(text) > 500 else "")
        )

        # 複製到剪貼簿
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._log("文字已複製到剪貼簿")

    def _on_file_received(self, sender_ip: str, sender_name: str, filepath: str, filesize: int):
        """收到檔案回調"""
        self.root.after(0, lambda: self._show_received_file(sender_ip, sender_name, filepath, filesize))

    def _show_received_file(self, sender_ip: str, sender_name: str, filepath: str, filesize: int):
        """顯示收到的檔案"""
        filename = os.path.basename(filepath)
        size_str = self._format_size(filesize)
        self._log(f"收到檔案: {filename} ({size_str}) 來自 {sender_name}")

        result = messagebox.askyesno(
            f"收到檔案 - 來自 {sender_name}",
            f"檔案: {filename}\n大小: {size_str}\n\n是否開啟檔案所在資料夾?"
        )
        if result:
            self._open_receive_folder()

    def _format_size(self, size: int) -> str:
        """格式化檔案大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _log(self, message: str):
        """寫入日誌"""
        def _write():
            self.log_text.config(state='normal')
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')

        self.root.after(0, _write)

    def _clear_log(self):
        """清除日誌"""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')

    def _open_receive_folder(self):
        """開啟接收資料夾"""
        os.makedirs(RECEIVE_DIR, exist_ok=True)
        import platform
        import subprocess

        if platform.system() == "Windows":
            os.startfile(RECEIVE_DIR)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", RECEIVE_DIR])
        else:  # Linux
            subprocess.run(["xdg-open", RECEIVE_DIR])

    def _on_close(self):
        """關閉視窗"""
        self.discovery.stop()
        self.server.stop()
        self.root.destroy()

    def run(self):
        """執行應用程式"""
        # 啟動網路服務
        self._log("正在啟動 PCPCS...")
        self.discovery.start()
        self.server.start()
        self._log(f"服務已啟動，正在掃描區域網路...")
        self._log(f"接收的檔案將儲存在: {RECEIVE_DIR}")

        # 執行主迴圈
        self.root.mainloop()


def main():
    app = PCPCSApp()
    app.run()


if __name__ == "__main__":
    main()
