"""
验证码服务
用于生成和验证验证码（用于密码重置等场景）
"""
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib


# 内存存储验证码（生产环境应使用 Redis）
_verification_codes: Dict[str, Dict] = {}


def generate_verification_code(length: int = 6) -> str:
    """
    生成数字验证码
    
    Args:
        length: 验证码长度，默认6位
        
    Returns:
        str: 验证码
    """
    return ''.join(random.choices(string.digits, k=length))


def generate_and_store_code(identifier: str, expire_minutes: int = 10) -> str:
    """
    生成并存储验证码
    
    Args:
        identifier: 标识符（如用户名、手机号、邮箱）
        expire_minutes: 过期时间（分钟），默认10分钟
        
    Returns:
        str: 生成的验证码
    """
    code = generate_verification_code()
    expire_time = datetime.now() + timedelta(minutes=expire_minutes)
    
    # 使用哈希存储，避免明文存储验证码
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    
    _verification_codes[identifier] = {
        "code_hash": code_hash,
        "expire_time": expire_time,
        "attempts": 0,  # 尝试次数
        "max_attempts": 5  # 最大尝试次数
    }
    
    return code


def verify_code(identifier: str, code: str) -> bool:
    """
    验证验证码
    
    Args:
        identifier: 标识符
        code: 用户输入的验证码
        
    Returns:
        bool: 验证是否成功
    """
    if identifier not in _verification_codes:
        return False
    
    code_info = _verification_codes[identifier]
    
    # 检查是否过期
    if datetime.now() > code_info["expire_time"]:
        del _verification_codes[identifier]
        return False
    
    # 检查尝试次数
    if code_info["attempts"] >= code_info["max_attempts"]:
        del _verification_codes[identifier]
        return False
    
    # 验证验证码
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    is_valid = code_hash == code_info["code_hash"]
    
    if not is_valid:
        # 增加尝试次数
        code_info["attempts"] += 1
    
    # 注意：验证成功后不在这里删除，由调用方决定何时清除
    # 这样可以支持一次性验证码和可重复使用的验证码
    
    return is_valid


def clear_code(identifier: str) -> bool:
    """
    清除验证码（用于验证成功后立即清除，防止重放攻击）
    
    Args:
        identifier: 标识符
        
    Returns:
        bool: 是否成功清除
    """
    if identifier in _verification_codes:
        del _verification_codes[identifier]
        return True
    return False


def get_code_for_testing(identifier: str) -> Optional[str]:
    """
    获取验证码（仅用于测试，生产环境不应暴露）
    注意：此函数仅用于开发测试，不应在生产环境使用
    """
    # 此函数仅用于开发测试
    # 生产环境应该通过短信或邮件发送验证码
    if identifier in _verification_codes:
        # 注意：这里无法返回原始验证码，因为只存储了哈希值
        # 实际使用中，验证码应该在生成时通过短信/邮件发送给用户
        return None
    return None


def clear_expired_codes():
    """清理过期的验证码"""
    now = datetime.now()
    expired_keys = [
        key for key, value in _verification_codes.items()
        if now > value["expire_time"]
    ]
    for key in expired_keys:
        del _verification_codes[key]

