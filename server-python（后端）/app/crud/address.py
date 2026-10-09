from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.address import UserAddress
from app.schemas.address import AddressCreate, AddressUpdate


class CRUDAddress(CRUDBase[UserAddress, AddressCreate]):
    def list_by_user(self, db: Session, user_id: int) -> List[UserAddress]:
        return db.query(UserAddress).filter(UserAddress.user_id == user_id).all()

    def get_user_address(self, db: Session, user_id: int, address_id: int) -> Optional[UserAddress]:
        return (
            db.query(UserAddress)
            .filter(UserAddress.user_id == user_id, UserAddress.address_id == address_id)
            .first()
        )

    def create_for_user(self, db: Session, user_id: int, obj_in: AddressCreate) -> UserAddress:
        from app.utils.pydantic import get_model_data
        data = get_model_data(obj_in)
        data["user_id"] = user_id
        if data.get("is_default") == 1:
            db.query(UserAddress).filter(UserAddress.user_id == user_id).update({"is_default": 0})
            db.commit()
        db_obj = UserAddress(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_for_user(
        self, db: Session, user_id: int, db_obj: UserAddress, obj_in: AddressUpdate
    ) -> UserAddress:
        from app.utils.pydantic import get_model_data
        data = get_model_data(obj_in, exclude_unset=True)
        if data.get("is_default") == 1:
            db.query(UserAddress).filter(UserAddress.user_id == user_id).update({"is_default": 0})
            db.commit()
        for k, v in data.items():
            setattr(db_obj, k, v)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


address = CRUDAddress(UserAddress)


