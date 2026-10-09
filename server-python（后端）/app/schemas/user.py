from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, field_serializer

from app.schemas.common import APIResponse, PageData


class UserRole(str, Enum):
    user = "user"
    merchant = "merchant"
    admin = "admin"


class UserBase(BaseModel):
    username: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[int] = 0
    student_no: Optional[str] = None
    department: Optional[str] = None
    role: UserRole = UserRole.user


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[int] = None
    student_no: Optional[str] = None
    department: Optional[str] = None


class UserOut(UserBase):
    user_id: int
    status: int
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True
    
    @field_serializer('avatar')
    def serialize_avatar(self, avatar: Optional[str], _info) -> Optional[str]:
        if not avatar:
            return avatar
        import re
        avatar = re.sub(r'^https?://[^/]+', '', avatar)
        avatar = re.sub(r'^(/uploads)+/', '/uploads/', avatar)
        if not avatar.startswith('/uploads/'):
            avatar = '/uploads/' + avatar.lstrip('/')
        return avatar


class UserAdminCanteenItem(BaseModel):
    canteen_id: int
    canteen_name: str


class UserAdminListItem(UserOut):
    order_count: int = 0
    last_login_time: Optional[datetime] = None
    canteen: Optional[UserAdminCanteenItem] = None


class UserAdminPageData(PageData[UserAdminListItem]):
    pass


class UserAdminListResponse(APIResponse[UserAdminPageData]):
    pass


class UserDetailOut(UserOut):
    order_count: int = 0
    last_login_time: Optional[datetime] = None


class UserDetailResponse(APIResponse[UserDetailOut]):
    pass


class UserStatusUpdate(BaseModel):
    status: int


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserBatchDelete(BaseModel):
    user_ids: list[int]


class UserBatchUpdate(BaseModel):
    user_ids: list[int]
    status: Optional[int] = None
    role: Optional[UserRole] = None
