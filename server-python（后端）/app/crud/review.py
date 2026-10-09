from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.review import Review
from app.schemas.review import ReviewCreate


class CRUDReview(CRUDBase[Review, ReviewCreate]):
    def list_by_dish(self, db: Session, dish_id: int) -> List[Review]:
        return (
            db.query(Review)
            .filter(Review.dish_id == dish_id)
            .order_by(Review.review_id.desc())
            .all()
        )


review = CRUDReview(Review)


