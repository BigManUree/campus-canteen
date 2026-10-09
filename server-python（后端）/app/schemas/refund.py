from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.schemas.common import APIResponse, PageData


class RefundCreate(BaseModel):
    order_id: int
    reason: str


class RefundUpdate(BaseModel):
    status: str
    admin_remark: Optional[str] = None


class RefundOut(BaseModel):
    refund_id: int
    order_id: int
    user_id: int
    refund_amount: float
    reason: Optional[str] = None
    status: str
    admin_remark: Optional[str] = None
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True


class RefundItemOut(BaseModel):
    item_id: Optional[int] = None
    dish_id: int
    dish_name: str
    price: float
    quantity: int
    remark: Optional[str] = None
    image: Optional[str] = None
    dish_image: Optional[str] = None


class RefundAdminListItem(BaseModel):
    refund_id: int
    order_id: int
    order_no: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    canteen_id: Optional[int] = None
    stall_name: Optional[str] = None
    refund_amount: float
    reason: Optional[str] = None
    reason_category: Optional[str] = None
    refund_items: Optional[str] = None
    items: List[RefundItemOut] = []
    order_items: List[RefundItemOut] = []
    status: str
    admin_remark: Optional[str] = None
    approve_time: Optional[datetime] = None
    auto_approved: bool = False
    create_time: datetime


class RefundDetailOut(BaseModel):
    refund_id: int
    order_id: int
    order_no: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    canteen_id: Optional[int] = None
    stall_name: Optional[str] = None
    refund_amount: float
    reason: Optional[str] = None
    reason_category: Optional[str] = None
    refund_items: Optional[str] = None
    items: List[RefundItemOut] = []
    order_items: List[RefundItemOut] = []
    status: str
    admin_remark: Optional[str] = None
    approve_time: Optional[datetime] = None
    auto_approved: bool = False
    create_time: datetime
    order_status: Optional[int] = None
    pay_status: Optional[int] = None
    order_amount: Optional[float] = None
    order_create_time: Optional[datetime] = None


class RefundAdminPageData(PageData[RefundAdminListItem]):
    pass


class RefundAdminListResponse(APIResponse[RefundAdminPageData]):
    pass


class RefundDetailResponse(APIResponse[RefundDetailOut]):
    pass


class RefundAuditRequest(BaseModel):
    action: str
    admin_remark: str


class RefundAuditResult(BaseModel):
    refund_id: int
    status: str
    admin_remark: Optional[str] = None
    approve_time: Optional[datetime] = None


class RefundAuditResponse(APIResponse[RefundAuditResult]):
    pass
