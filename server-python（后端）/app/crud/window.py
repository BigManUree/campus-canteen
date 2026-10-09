from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.window import Window
from app.models.dish import Dish
from app.schemas.window import WindowCreate, WindowUpdate


class CRUDWindow(CRUDBase[Window, WindowCreate]):
    def list_all(self, db: Session) -> List[Window]:
        """获取全部窗口，按排序值和窗口 ID 稳定排序。"""
        return db.query(Window).order_by(Window.sort_order, Window.window_id).all()

    def list_by_parent(self, db: Session, parent_id: int = 0) -> List[Window]:
        """查询指定父级下的窗口列表，用于组织一级窗口和子窗口。"""
        return db.query(Window).filter(
            Window.parent_id == parent_id
        ).order_by(Window.sort_order, Window.window_id).all()

    def list_by_canteen(self, db: Session, canteen_id: int) -> List[Window]:
        """查询指定食堂下的顶级窗口列表。"""
        return db.query(Window).filter(
            Window.canteen_id == canteen_id,
            Window.parent_id == 0,
        ).order_by(Window.sort_order, Window.window_id).all()

    def get_by_name(self, db: Session, name: str, canteen_id: Optional[int] = None) -> Optional[Window]:
        """按窗口名称查询，可传入食堂 ID 限定唯一性范围。"""
        query = db.query(Window).filter(Window.window_name == name)
        if canteen_id is not None:
            query = query.filter(Window.canteen_id == canteen_id)
        return query.first()

    def search_windows(
        self,
        db: Session,
        *,
        canteen_id: Optional[int] = None,
        keyword: Optional[str] = None,
        parent_id: Optional[int] = 0,
    ):
        """按食堂、父级和关键字组合构建窗口查询，供列表接口继续分页。"""
        query = db.query(Window)
        if canteen_id is not None:
            query = query.filter(Window.canteen_id == canteen_id)
        if parent_id is not None:
            query = query.filter(Window.parent_id == parent_id)
        if keyword:
            query = query.filter(Window.window_name.like(f"%{keyword.strip()}%"))
        return query

    def has_dishes(self, db: Session, window_id: int) -> bool:
        """判断窗口下是否仍有关联菜品，删除窗口前用于业务校验。"""
        return db.query(func.count(Dish.dish_id)).filter(Dish.window_id == window_id).scalar() > 0


window = CRUDWindow(Window)
