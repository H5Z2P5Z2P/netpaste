import hashlib
import secrets
from datetime import datetime

def generate_note_id() -> str:
    """生成16位剪贴板ID"""
    return secrets.token_hex(8)

def generate_token() -> str:
    """生成32位token"""
    return secrets.token_hex(16)

def generate_req_id() -> str:
    """生成请求ID"""
    return secrets.token_hex(10)

def get_current_time() -> str:
    """获取当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def mask_ip(ip: str) -> str:
    """掩码IP地址"""
    parts = ip.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.**.{parts[3]}"
    return ip