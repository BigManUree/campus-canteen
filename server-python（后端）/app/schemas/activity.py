from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ActivityBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    organizer: Optional[str] = None
    location: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: Optional[int] = 1
    sort_order: Optional[int] = 0


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    organizer: Optional[str] = None
    location: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[int] = None
    sort_order: Optional[int] = None


class ActivityOut(BaseModel):
    activity_id: int
    title: str
    subtitle: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    organizer: Optional[str] = None
    location: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: int
    sort_order: int
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True
