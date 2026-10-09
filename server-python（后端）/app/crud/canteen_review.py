from typing import List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.canteen_review import CanteenReview
from app.schemas.canteen_review import CanteenReviewCreate


class CRUDCanteenReview(CRUDBase[CanteenReview, CanteenReviewCreate]):
    def list_by_canteen(self, db: Session, canteen_id: int) -> List[CanteenReview]:
        return db.query(CanteenReview).filter(
            CanteenReview.canteen_id == canteen_id
        ).order_by(CanteenReview.create_time.desc()).all()


canteen_review = CRUDCanteenReview(CanteenReview)

