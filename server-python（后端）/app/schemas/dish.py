from datetime import datetime, timedelta
from typing import Optional
import json

from pydantic import BaseModel, computed_field, ConfigDict


class DishBase(BaseModel):
    canteen_id: int
    window_id: int = 0
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    spicy_level: int = 0
    allergen: Optional[str] = None
    calorie: Optional[int] = None
    images: Optional[str] = None
    stock: int = 999
    warning_stock: int = 10
    media_path: Optional[str] = None
    media_type: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class DishCreate(DishBase):
    pass


class DishUpdate(BaseModel):
    canteen_id: Optional[int] = None
    window_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    spicy_level: Optional[int] = None
    allergen: Optional[str] = None
    calorie: Optional[int] = None
    images: Optional[str] = None
    stock: Optional[int] = None
    warning_stock: Optional[int] = None
    status: Optional[int] = None
    media_path: Optional[str] = None
    media_type: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class DishStatusUpdate(BaseModel):
    status: int


class DishOut(BaseModel):
    dish_id: int
    canteen_id: int
    window_id: Optional[int] = 0
    window_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    spicy_level: int = 0
    allergen: Optional[str] = None
    calorie: Optional[int] = None
    images: Optional[str] = None
    stock: int
    warning_stock: int = 10
    sales: int = 0
    status: int
    media_path: Optional[str] = None
    media_type: Optional[str] = None
    view_count: int = 0
    favorite_count: int = 0
    create_time: datetime
    update_time: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @computed_field
    @property
    def is_new(self) -> bool:
        return (datetime.now() - self.create_time).days <= 7

    @computed_field
    @property
    def is_hot(self) -> bool:
        return self.sales >= 50

    @computed_field
    @property
    def is_recommend(self) -> bool:
        return self.favorite_count >= 20

    @computed_field
    @property
    def image_urls(self) -> list[str]:
        from app.utils.image import convert_images_to_full_urls
        return convert_images_to_full_urls(self.images)

