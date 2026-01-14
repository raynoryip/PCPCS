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
BUFFER_SIZE = 65536             # 傳輸緩衝區大小 (64KB for better throughput)
FILE_CHUNK_SIZE = 1048576       # 檔案分塊大小 (1MB for maximum speed)

# Socket 優化參數
SOCKET_SEND_BUFFER = 2097152    # 發送緩衝區 2MB
SOCKET_RECV_BUFFER = 2097152    # 接收緩衝區 2MB

# 訊息類型
MSG_TYPE_DISCOVERY = "PCPCS_DISCOVERY"
MSG_TYPE_RESPONSE = "PCPCS_RESPONSE"
MSG_TYPE_TEXT = "TEXT"
MSG_TYPE_FILE = "FILE"
MSG_TYPE_FILE_CHUNK = "FILE_CHUNK"
MSG_TYPE_FILE_END = "FILE_END"

# 資料夾傳輸訊息類型
MSG_TYPE_FOLDER_START = "FOLDER_START"
MSG_TYPE_FOLDER_FILE = "FOLDER_FILE"
MSG_TYPE_FOLDER_END = "FOLDER_END"

# 回應類型 (固定 8 bytes 避免 TCP 黏包)
RESP_LENGTH = 8            # 回應固定長度
RESP_ACK = "ACK".ljust(RESP_LENGTH, '_')      # 發送用: "ACK_____"
RESP_SKIP = "SKIP".ljust(RESP_LENGTH, '_')    # 發送用: "SKIP____"
RESP_ERROR = "ERROR".ljust(RESP_LENGTH, '_')  # 發送用: "ERROR___"
# 比對用 (去掉填充)
RESP_ACK_STRIPPED = "ACK"
RESP_SKIP_STRIPPED = "SKIP"
RESP_ERROR_STRIPPED = "ERROR"

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

def get_receive_dir():
    """取得接收目錄路徑（跨平台）"""
    if platform.system() == "Windows":
        # Windows 使用 USERPROFILE 環境變數
        home = os.environ.get('USERPROFILE', os.path.expanduser("~"))
    else:
        home = os.path.expanduser("~")
    return os.path.join(home, "PCPCS_Received")

RECEIVE_DIR = get_receive_dir()
