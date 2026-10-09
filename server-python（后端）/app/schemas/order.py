from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, field_validator

from app.schemas.common import APIResponse, PageData


class OrderItemIn(BaseModel):
    dish_id: int
    quantity: int
    remark: Optional[str] = None


class OrderCreate(BaseModel):
    canteen_id: int
    order_type: str = "pickup"
    pickup_time: Optional[Union[datetime, str]] = None
    delivery_address: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    remark: Optional[str] = None
    items: List[OrderItemIn]
    coupon_id: Optional[int] = None  # 优惠券ID
    
    @field_validator('pickup_time', mode='before')
    @classmethod
    def parse_pickup_time(cls, v):
        """解析取餐时间，支持多种格式"""
        if v is None or v == "" or v == "null":
            return None
        
        if isinstance(v, datetime):
            return v
        
        if isinstance(v, str):
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
            
            return None
        
        return v


class OrderStatusUpdate(BaseModel):
    order_status: int


class OrderMockPayRequest(BaseModel):
    order_status: int = 0
    pay_status: int = 1


class OrderItemOut(BaseModel):
    item_id: int
    dish_id: int
    dish_name: str
    price: float
    quantity: int
    remark: Optional[str] = None
    image: Optional[str] = None

    class Config:
        from_attributes = True


class OrderAdminItemOut(BaseModel):
    item_id: Optional[int] = None
    dish_id: int
    dish_name: str
    price: float
    quantity: int
    remark: Optional[str] = None
    image: Optional[str] = None


class CanteenInfo(BaseModel):
    canteen_id: int
    canteen_name: str
    building: Optional[str] = None
    floor: Optional[str] = None
    window_no: Optional[str] = None
    contact_phone: Optional[str] = None

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    order_id: int
    order_no: str
    user_id: int
    canteen_id: int
    canteen: Optional[CanteenInfo] = None
    order_type: str
    total_amount: float
    discount_amount: float = 0
    pay_amount: float
    pay_status: int
    pay_time: Optional[datetime] = None
    order_status: int
    pickup_code: Optional[str] = None
    pickup_time: Optional[datetime] = None
    verify_time: Optional[datetime] = None
    accept_time: Optional[datetime] = None
    ready_time: Optional[datetime] = None
    complete_time: Optional[datetime] = None
    cancel_time: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    remark: Optional[str] = None
    create_time: datetime
    update_time: datetime
    is_reviewed: bool = False
    items: List[OrderItemOut] = []

    class Config:
        from_attributes = True


class OrderAdminListItem(BaseModel):
    order_id: int
    order_no: str
    user_id: int
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    canteen_id: int
    stall_name: Optional[str] = None
    order_type: str
    pay_amount: float
    total_amount: float
    pay_status: int
    order_status: int
    create_time: datetime
    pay_time: Optional[datetime] = None
    complete_time: Optional[datetime] = None
    items: List[OrderAdminItemOut] = []


class OrderAdminPageData(PageData[OrderAdminListItem]):
    pass


class OrderStatusSummaryOut(BaseModel):
    pending: int = 0
    preparing: int = 0
    ready: int = 0
    delivering: int = 0
    refund: int = 0


class OrderStatusViewedIn(BaseModel):
    scope: str

    @field_validator('scope')
    @classmethod
    def validate_scope(cls, v):
        allowed = {'all', 'pending', 'preparing', 'ready', 'delivering', 'refund'}
        if v not in allowed:
            raise ValueError('scope 不合法')
        return v


class OrderAdminListResponse(APIResponse[OrderAdminPageData]):
    pass


class TimelineEvent(BaseModel):
    status: int
    status_name: str
    timestamp: datetime
    operator_name: Optional[str] = None
    description: Optional[str] = None
    is_current: bool = False

    class Config:
        from_attributes = True


class OrderTimeline(BaseModel):
    order_id: int
    order_no: str
    current_status: int
    current_status_name: str
    timeline: List[TimelineEvent]

    class Config:
        from_attributes = True


class OrderCancelRequest(BaseModel):
    reason: str
    cancel_reason: Optional[str] = None


class OrderCancelResponse(BaseModel):
    success: bool
    message: str
    refund_amount: Optional[float] = None
    refund_id: Optional[int] = None
    order_id: int
    order_status: Optional[int] = None
    need_approval: bool = False

    class Config:
        from_attributes = True
