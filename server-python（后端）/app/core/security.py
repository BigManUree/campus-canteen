from datetime import datetime, timedelta
from typing import Any, Dict

from jose import JWTError, jwt
import bcrypt as bcrypt_lib

from app.core.config import get_settings

settings = get_settings()
ALGORITHM = "HS256"


def create_token(data: Dict[str, Any], expires_seconds: int = settings.jwt_expire) -> str:
    """根据业务载荷生成带过期时间的 JWT 访问令牌。"""
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(seconds=expires_seconds)})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """解码并验证 JWT 令牌，签名或过期时间无效时由 jose 抛出异常。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def hash_password(password: str) -> str:
    """使用bcrypt库直接哈希密码"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt_lib.gensalt()
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """验证密码"""
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt_lib.checkpw(password_bytes, hashed_bytes)

