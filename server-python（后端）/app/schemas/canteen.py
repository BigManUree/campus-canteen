from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel


class CanteenBase(BaseModel):
    canteen_name: str
    building: str
    floor: Optional[str] = None
    window_no: Optional[str] = None
    service_type: Optional[str] = "pickup"
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_person: Optional[str] = None
    description: Optional[str] = None
    rest_days: Optional[str] = None
    sort_order: Optional[int] = 0
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    address: Optional[str] = None
    avatar: Optional[str] = None
    notice: Optional[str] = None
    notice_enabled: Optional[bool] = True
    location: Optional[str] = None
    business_hours: Optional[str] = None
    avg_price: Optional[Decimal] = None
    status: Optional[int] = 1


class CanteenCreate(CanteenBase):
    pass


class CanteenUpdate(BaseModel):
    canteen_name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    window_no: Optional[str] = None
    service_type: Optional[str] = None
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_person: Optional[str] = None
    description: Optional[str] = None
    rest_days: Optional[str] = None
    sort_order: Optional[int] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    address: Optional[str] = None
    avatar: Optional[str] = None
    notice: Optional[str] = None
    notice_enabled: Optional[bool] = None
    location: Optional[str] = None
    business_hours: Optional[str] = None
    avg_price: Optional[Decimal] = None
    status: Optional[int] = None


class CanteenOut(CanteenBase):
    canteen_id: int
    merchant_user_id: Optional[int] = None
    window_count: int = 0
    create_time: datetime

    class Config:
        from_attributes = True

