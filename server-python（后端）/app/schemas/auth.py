from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    username: str = Field(..., min_length=1, description="用户名或手机号")


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str
    verification_code: str | None = None
    expires_in: int | None = None


class ResetPasswordRequest(BaseModel):
    username: str = Field(..., min_length=1, description="用户名或手机号")
    verification_code: str = Field(..., min_length=4, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=50)


class TokenResponse(BaseModel):
    token: str
    expireIn: int
    userInfo: UserOut

