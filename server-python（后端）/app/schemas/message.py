from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageCreate(BaseModel):
    to_user_id: int
    order_id: Optional[int] = None
    content: str
    type: int = 1


class MessageOut(BaseModel):
    message_id: int
    from_user_id: int
    to_user_id: int
    order_id: Optional[int] = None
    content: str
    type: int
    is_read: int
    create_time: datetime

    class Config:
        from_attributes = True


