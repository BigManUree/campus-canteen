from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Optional

from app.core.security import decode_token
from app.crud import user as user_crud
from app.db.session import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_db():
    """为每个请求创建数据库会话，并在请求结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """解析并校验登录用户，认证失败或用户禁用时抛出 HTTP 异常。"""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证令牌")
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        # JWT的subject是字符串，需要转换为整数
        if isinstance(user_id, str):
            user_id = int(user_id)
    except (JWTError, ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 无效")
    user = user_crud.user.get(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if user.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已禁用")
    return user


def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """可选的用户认证，如果没有token则返回None"""
    if not token:
        return None
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        # JWT的subject是字符串，需要转换为整数
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        user = user_crud.user.get(db, user_id)
        if user and user.status == 1:
            return user
    except (JWTError, ValueError, TypeError):
        pass
    
    return None


def require_admin(current=Depends(get_current_user)):
    """仅超级管理员可访问"""
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current


def require_merchant(current=Depends(get_current_user)):
    """商家或超级管理员可访问"""
    if current.role not in ("merchant", "admin"):
        raise HTTPException(status_code=403, detail="需要商家或超级管理员权限")
    return current


def require_student(current=Depends(get_current_user)):
    """已登录用户可访问"""
    return current


def is_admin_role(role: str) -> bool:
    """判断是否为超级管理员角色"""
    return role == "admin"


def is_merchant_role(role: str) -> bool:
    """判断是否为商家角色"""
    return role == "merchant"


def get_role_label(role: str) -> str:
    """获取角色中文名称"""
    role_map = {
        "user": "用户",
        "merchant": "商家",
        "admin": "超级管理员",
    }
    return role_map.get(role, "未知")

