from typing import List, Optional

from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.crud.base import CRUDBase
from app.models.favorite import Favorite


# 创建一个简单的 schema 用于 CRUDBase
class FavoriteCreate(BaseModel):
    user_id: int
    dish_id: int


class CRUDFavorite(CRUDBase[Favorite, FavoriteCreate]):
    def get_by_user_and_dish(self, db: Session, user_id: int, dish_id: int) -> Optional[Favorite]:
        return (
            db.query(Favorite)
            .filter(Favorite.user_id == user_id, Favorite.dish_id == dish_id)
            .first()
        )

    def list_by_user(self, db: Session, user_id: int) -> List[Favorite]:
        return db.query(Favorite).filter(Favorite.user_id == user_id).all()


favorite = CRUDFavorite(Favorite)


