import json
from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate
from app.utils.pydantic import get_model_data


class CRUDActivity(CRUDBase[Activity, ActivityCreate]):
    def list_active(self, db: Session) -> List[Activity]:
        return db.query(Activity).filter(
            Activity.status == 1
        ).order_by(Activity.sort_order.desc(), Activity.start_time.desc(), Activity.activity_id.desc()).all()

    def create(self, db: Session, obj_in: ActivityCreate) -> Activity:
        obj_data = get_model_data(obj_in)
        if "target_canteen_ids" in obj_data and obj_data["target_canteen_ids"] is not None:
            obj_data["target_canteen_ids"] = json.dumps(obj_data["target_canteen_ids"])

        db_obj = Activity(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


activity = CRUDActivity(Activity)
