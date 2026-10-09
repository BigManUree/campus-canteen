from typing import Any, Generic, Optional, Type, TypeVar, Dict

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import Base
from app.utils.pydantic import get_model_data

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """保存当前 CRUD 实例绑定的 SQLAlchemy 模型类。"""
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """按主键查询单条记录，不存在时返回 None。"""
        return db.query(self.model).get(id)

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """创建记录，在 CRUD 层提交事务"""
        obj_data = get_model_data(obj_in)
        db_obj = self.model(**obj_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def create_by_dict(self, db: Session, obj_data: Dict[str, Any]) -> ModelType:
        """通过字典创建记录，在 CRUD 层提交事务"""
        db_obj = self.model(**obj_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, id: Any, obj_in: BaseModel) -> Optional[ModelType]:
        """更新记录，在 CRUD 层提交事务"""
        db_obj = self.get(db, id)
        if not db_obj:
            return None
        
        update_data = get_model_data(obj_in)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_by_dict(self, db: Session, id: Any, update_data: Dict[str, Any]) -> Optional[ModelType]:
        """通过字典更新记录，在 CRUD 层提交事务"""
        db_obj = self.get(db, id)
        if not db_obj:
            return None
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: Any) -> bool:
        """删除记录，在 CRUD 层提交事务"""
        db_obj = self.get(db, id)
        if not db_obj:
            return False
        
        db.delete(db_obj)
        db.commit()
        return True

