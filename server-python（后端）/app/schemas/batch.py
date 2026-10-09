from pydantic import BaseModel, Field
from typing import Optional


class BatchUpdateStatusRequest(BaseModel):
    """批量更新状态请求"""
    dish_ids: list[int] = Field(..., description="菜品ID列表")
    status: int = Field(..., description="目标状态（0=下架，1=上架）")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    dish_ids: list[int] = Field(..., description="菜品ID列表")


class BatchUpdatePriceRequest(BaseModel):
    """批量修改价格请求"""
    dish_ids: list[int] = Field(..., description="菜品ID列表")
    price_type: str = Field(..., description="价格类型：fixed, increase, decrease, percent")
    price_value: float = Field(..., description="价格值")


class BatchExportRequest(BaseModel):
    """批量导出请求"""
    dish_ids: Optional[list[int]] = Field(None, description="菜品ID列表（可选）")
    format: str = Field("excel", description="导出格式：excel 或 csv")
    fields: Optional[list[str]] = Field(None, description="导出字段列表（可选）")


class BatchExportOrdersRequest(BaseModel):
    """批量导出订单请求"""
    order_ids: Optional[list[int]] = Field(None, description="订单ID列表（可选）")
    start_date: Optional[str] = Field(None, description="开始日期（YYYY-MM-DD）")
    end_date: Optional[str] = Field(None, description="结束日期（YYYY-MM-DD）")
    order_status: Optional[int] = Field(None, description="订单状态")
    pay_status: Optional[int] = Field(None, description="支付状态")
    format: str = Field("excel", description="导出格式：excel 或 csv")

