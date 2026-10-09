from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api import deps
from app.api.decorators import handle_api_errors
from app.core.security import create_token, verify_password
from app.crud import user as user_crud
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
)
from app.schemas.user import UserCreate, UserOut, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/register", response_model=TokenResponse)
@handle_api_errors("注册失败")
def register(payload: UserCreate, db: Session = Depends(deps.get_db)):
    """用户注册
    
    - 默认注册为 user（用户）角色
    - 如果系统中没有 admin，第一个注册的用户自动成为 admin
    """
    if user_crud.user.get_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    from app.models.user import User
    has_admin = db.query(User).filter(User.role == "admin").first() is not None
    
    if not has_admin:
        admin_payload = payload.model_copy(update={"role": UserRole.admin})
        user = user_crud.user.create(db, admin_payload)
    else:
        user_payload = payload.model_copy(update={"role": UserRole.user})
        user = user_crud.user.create(db, user_payload)
    
    token = create_token({"sub": str(user.user_id)})
    user_info = UserOut.model_validate(user)
    return TokenResponse(token=token, expireIn=7200, userInfo=user_info)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(deps.get_db)):
    user = user_crud.user.get_by_username(db, payload.username)
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=400, detail="账号或密码错误")
    token = create_token({"sub": str(user.user_id)})
    return TokenResponse(token=token, expireIn=7200, userInfo=UserOut.model_validate(user))


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@handle_api_errors("发送验证码失败")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(deps.get_db)):
    """忘记密码：按用户名或手机号发送验证码。"""
    from app.services import verification
    from app.core.config import get_settings

    identifier = payload.username.strip()
    user = user_crud.user.get_by_username_or_phone(db, identifier)

    if not user:
        raise HTTPException(status_code=404, detail="该手机号或用户名未注册")

    code = verification.generate_and_store_code(identifier, expire_minutes=10)

    settings = get_settings()
    verification_code: Optional[str] = code if settings.env == "development" else None

    return ForgotPasswordResponse(
        success=True,
        message="验证码已发送，请查收",
        verification_code=verification_code,
        expires_in=600,
    )


@router.post("/reset-password")
@handle_api_errors("重置密码失败")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(deps.get_db)):
    """重置密码。"""
    from app.services import verification

    identifier = payload.username.strip()
    user = user_crud.user.get_by_username_or_phone(db, identifier)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not verification.verify_code(identifier, payload.verification_code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    verification.clear_code(identifier)
    user_crud.user.update_password(db, user.user_id, payload.new_password)

    return {"success": True, "message": "密码重置成功"}


@router.post("/create-merchant", response_model=TokenResponse)
@handle_api_errors("创建商家账号失败")
def create_merchant(
    payload: UserCreate,
    canteen_id: Optional[int] = None,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """超级管理员创建商家账号（可同时绑定食堂）
    
    创建一个角色为 merchant 的用户账号。
    如果提供了 canteen_id，会同时将该食堂绑定到新商家。
    """
    if user_crud.user.get_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    merchant_payload = payload.model_copy(update={"role": UserRole.merchant})
    user = user_crud.user.create(db, merchant_payload)
    
    if canteen_id:
        from app.models.canteen import Canteen
        canteen = db.query(Canteen).filter(Canteen.canteen_id == canteen_id).first()
        if not canteen:
            raise HTTPException(status_code=404, detail=f"食堂 {canteen_id} 不存在")
        db.query(Canteen).filter(
            Canteen.merchant_user_id == user.user_id,
            Canteen.canteen_id != canteen_id
        ).update({"merchant_user_id": None}, synchronize_session=False)
        canteen.merchant_user_id = user.user_id
        db.commit()
    
    token = create_token({"sub": str(user.user_id)})
    user_info = UserOut.model_validate(user)
    return TokenResponse(token=token, expireIn=7200, userInfo=user_info)


@router.post("/register-admin", response_model=TokenResponse)
@handle_api_errors("管理员注册失败")
def register_admin(
    payload: UserCreate,
    admin_key: str,
    db: Session = Depends(deps.get_db)
):
    """管理员注册接口"""
    from app.core.config import get_settings
    
    settings = get_settings()
    
    if not settings.admin_register_key:
        raise HTTPException(
            status_code=403,
            detail="管理员注册功能未启用，请先配置 ADMIN_REGISTER_KEY 环境变量"
        )
    
    if admin_key != settings.admin_register_key:
        raise HTTPException(status_code=403, detail="管理员注册密钥错误")
    
    if user_crud.user.get_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    admin_payload = payload.model_copy(update={"role": UserRole.admin})
    user = user_crud.user.create(db, admin_payload)
    
    token = create_token({"sub": str(user.user_id)})
    user_info = UserOut.model_validate(user)
    return TokenResponse(token=token, expireIn=7200, userInfo=user_info)
