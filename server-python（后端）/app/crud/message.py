from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.message import Message
from app.schemas.message import MessageCreate


class CRUDMessage(CRUDBase[Message, MessageCreate]):
    def list_for_user(self, db: Session, user_id: int) -> List[Message]:
        """查询指定用户收到的消息，并按最新消息优先排序。"""
        return (
            db.query(Message)
            .filter(Message.to_user_id == user_id)
            .order_by(Message.message_id.desc())
            .all()
        )
    
    def mark_all_as_read(self, db: Session, user_id: int) -> int:
        """批量标记用户的所有消息为已读，返回更新的数量"""
        count = db.query(Message).filter(
            Message.to_user_id == user_id,
            Message.is_read == 0
        ).update({"is_read": 1})
        db.commit()
        return count
    
    def create_batch(self, db: Session, messages_data: List[dict]) -> List[Message]:
        """批量创建消息"""
        messages = [Message(**data) for data in messages_data]
        db.add_all(messages)
        db.commit()
        for msg in messages:
            db.refresh(msg)
        return messages


message = CRUDMessage(Message)


