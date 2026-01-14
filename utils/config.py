"""
PCPCS Configuration
跨平台 P2P 通訊系統配置
"""
import socket
import platform

# 網路設定
DISCOVERY_PORT = 52525          # UDP 廣播端口
TRANSFER_PORT = 52526           # TCP 傳輸端口
BROADCAST_INTERVAL = 3          # 廣播間隔(秒)
PING_TIMEOUT = 2                # Ping 超時(秒)
BUFFER_SIZE = 8192              # 傳輸緩衝區大小
FILE_CHUNK_SIZE = 65536         # 檔案分塊大小

# 訊息類型
MSG_TYPE_DISCOVERY = "PCPCS_DISCOVERY"
MSG_TYPE_RESPONSE = "PCPCS_RESPONSE"
MSG_TYPE_TEXT = "TEXT"
MSG_TYPE_FILE = "FILE"
MSG_TYPE_FILE_CHUNK = "FILE_CHUNK"
MSG_TYPE_FILE_END = "FILE_END"

# 取得本機資訊
def get_hostname():
    return socket.gethostname()

def get_platform():
    return platform.system()

def get_local_ip():
    """取得本機 IP 位址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# 預設接收目錄
import os
RECEIVE_DIR = os.path.join(os.path.expanduser("~"), "PCPCS_Received")
