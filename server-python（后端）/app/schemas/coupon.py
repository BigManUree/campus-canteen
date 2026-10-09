from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CouponBase(BaseModel):
    name: str
    description: Optional[str] = None
    coupon_type: str = "discount"  # discount 或 cash
    discount_value: Decimal = Field(..., gt=Decimal("0"))
    min_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    max_discount: Optional[Decimal] = None
    total_count: int = -1
    start_time: datetime
    end_time: datetime

    @field_validator("coupon_type")
    @classmethod
    def validate_coupon_type(cls, value: str) -> str:
        if value not in {"discount", "cash"}:
            raise ValueError("优惠券类型必须为 discount 或 cash")
        return value

    @field_validator("max_discount")
    @classmethod
    def validate_max_discount(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value < 0:
            raise ValueError("最大优惠金额不能小于 0")
        return value

    @field_validator("total_count")
    @classmethod
    def validate_total_count(cls, value: int) -> int:
        if value == 0 or value < -1:
            raise ValueError("发放总量必须为 -1（不限量）或大于 0")
        return value

    @model_validator(mode="after")
    def validate_coupon_rules(self):
        if self.coupon_type == "discount" and self.discount_value > Decimal("10"):
            raise ValueError("折扣券优惠值请填写 0-10，例如 8 表示 8 折，0.8 表示 8 折")
        if self.end_time <= self.start_time:
            raise ValueError("失效时间必须晚于生效时间")
        return self


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    coupon_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    min_amount: Optional[Decimal] = None
    max_discount: Optional[Decimal] = None
    total_count: Optional[int] = None
    status: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @field_validator("coupon_type")
    @classmethod
    def validate_coupon_type(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in {"discount", "cash"}:
            raise ValueError("优惠券类型必须为 discount 或 cash")
        return value

    @field_validator("discount_value")
    @classmethod
    def validate_discount_value(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value <= 0:
            raise ValueError("优惠值必须大于 0")
        return value

    @field_validator("min_amount")
    @classmethod
    def validate_min_amount(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value < 0:
            raise ValueError("最低消费金额不能小于 0")
        return value

    @field_validator("max_discount")
    @classmethod
    def validate_max_discount(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value < 0:
            raise ValueError("最大优惠金额不能小于 0")
        return value

    @field_validator("total_count")
    @classmethod
    def validate_total_count(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and (value == 0 or value < -1):
            raise ValueError("发放总量必须为 -1（不限量）或大于 0")
        return value

    @model_validator(mode="after")
    def validate_coupon_rules(self):
        if self.coupon_type == "discount" and self.discount_value is not None and self.discount_value > Decimal("10"):
            raise ValueError("折扣券优惠值请填写 0-10，例如 8 表示 8 折，0.8 表示 8 折")
        if self.start_time is not None and self.end_time is not None and self.end_time <= self.start_time:
            raise ValueError("失效时间必须晚于生效时间")
        return self


class CouponOut(BaseModel):
    coupon_id: int
    name: str
    description: Optional[str] = None
    coupon_type: str
    discount_value: float
    min_amount: float
    max_discount: Optional[float] = None
    total_count: int
    used_count: int
    claimed_count: int = 0
    start_time: datetime
    end_time: datetime
    status: int
    create_time: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCouponOut(BaseModel):
    id: int
    user_id: int
    coupon_id: int
    status: int
    used_time: Optional[datetime] = None
    used_order_id: Optional[int] = None
    get_time: datetime
    expire_time: datetime
    coupon: Optional[CouponOut] = None

    model_config = ConfigDict(from_attributes=True)
