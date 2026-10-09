from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FAQBase(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    sort_order: Optional[int] = 0
    status: Optional[int] = 1


class FAQCreate(FAQBase):
    pass


class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[int] = None


class FAQOut(FAQBase):
    faq_id: int
    view_count: int
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True

