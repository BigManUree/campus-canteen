from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.dish import Dish
from app.schemas.dish import DishCreate, DishUpdate


class CRUDDish(CRUDBase[Dish, DishCreate]):
    def list_active(self, db: Session) -> List[Dish]:
        return db.query(Dish).filter(Dish.status == 1).all()

    def get_multi_by_ids(self, db: Session, ids: List[int]) -> List[Dish]:
        return db.query(Dish).filter(Dish.dish_id.in_(ids)).all()
    
    def update_status(self, db: Session, id: int, status: int) -> Optional[Dish]:
        """更新菜品状态"""
        return self.update_by_dict(db, id, {"status": status})
    
    def increment_view_count(self, db: Session, id: int) -> Optional[Dish]:
        """增加浏览量"""
        dish = self.get(db, id)
        if dish:
            dish.view_count = (dish.view_count or 0) + 1
            db.commit()
            db.refresh(dish)
        return dish


dish = CRUDDish(Dish)

