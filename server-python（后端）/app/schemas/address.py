from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AddressBase(BaseModel):
    receiver: str
    phone: str
    building: str
    room: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: int = 0


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    receiver: Optional[str] = None
    phone: Optional[str] = None
    building: Optional[str] = None
    room: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: Optional[int] = None


class AddressOut(AddressBase):
    address_id: int
    user_id: int
    create_time: datetime

    class Config:
        from_attributes = True


