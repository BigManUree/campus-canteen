"""
通用响应模型
用于统一 API 响应格式
"""
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    code: int = Field(200, description="状态码，200 表示成功")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {}
            }
        }

    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "APIResponse[T]":
        """创建成功响应"""
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: int = 400) -> "APIResponse[None]":
        """创建错误响应"""
        return cls(code=code, message=message, data=None)


class PageData(BaseModel, Generic[T]):
    """统一分页 data 结构"""
    records: List[T] = Field(..., description="当前页数据列表")
    total: int = Field(..., ge=0, description="总记录数")
    pageNum: int = Field(..., ge=1, description="当前页码")
    pageSize: int = Field(..., ge=1, description="每页数量")
    totalPages: int = Field(..., ge=0, description="总页数")

    class Config:
        json_schema_extra = {
            "example": {
                "records": [],
                "total": 0,
                "pageNum": 1,
                "pageSize": 20,
                "totalPages": 0
            }
        }

    @classmethod
    def create(
        cls,
        records: List[T],
        total: int,
        page_num: int,
        page_size: int
    ) -> "PageData[T]":
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            records=records,
            total=total,
            pageNum=page_num,
            pageSize=page_size,
            totalPages=total_pages
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """兼容旧接口的分页响应格式"""
    items: List[T] = Field(..., description="当前页数据列表")
    total: int = Field(..., ge=0, description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, description="每页数量")
    total_pages: int = Field(..., ge=0, description="总页数")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0
            }
        }

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页数量，最大100")

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """返回限制数量"""
        return self.page_size

