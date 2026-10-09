from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.crud.base import CRUDBase
from app.models.cart import CartItem
from app.schemas.cart import CartItemIn
from app.models.dish import Dish


class CRUDCart(CRUDBase[CartItem, CartItemIn]):
    def list_by_user(self, db: Session, user_id: int) -> List[CartItem]:
        """查询用户购物车，并预加载菜品信息以减少接口序列化时的额外查询。"""
        return (
            db.query(CartItem)
            .options(joinedload(CartItem.dish))
            .filter(CartItem.user_id == user_id)
            .order_by(CartItem.create_time.desc())
            .all()
        )

    def get_user_item(self, db: Session, user_id: int, item_id: int) -> Optional[CartItem]:
        """按购物车项 ID 和用户 ID 查询，避免用户访问他人的购物车项。"""
        return (
            db.query(CartItem)
            .filter(CartItem.user_id == user_id, CartItem.item_id == item_id)
            .first()
        )

    def add_or_update(self, db: Session, user_id: int, obj_in: CartItemIn) -> CartItem:
        """添加菜品到购物车；若同一菜品已存在，则更新数量、备注和价格快照。"""
        dish: Dish | None = db.query(Dish).filter(Dish.dish_id == obj_in.dish_id).first()
        if not dish or dish.status != 1:
            raise ValueError("dish_not_found")
        exist = (
            db.query(CartItem)
            .filter(CartItem.user_id == user_id, CartItem.dish_id == obj_in.dish_id)
            .first()
        )
        # 修复：统一使用元为单位，与菜品表保持一致
        price = float(dish.price)
        if exist:
            exist.quantity = obj_in.quantity
            exist.remark = obj_in.remark
            exist.dish_name = dish.name
            exist.price = price
            db.add(exist)
            db.commit()
            db.refresh(exist)
            return exist
        item = CartItem(
            user_id=user_id,
            dish_id=dish.dish_id,
            dish_name=dish.name,
            price=price,
            quantity=obj_in.quantity,
            remark=obj_in.remark,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


cart = CRUDCart(CartItem)


