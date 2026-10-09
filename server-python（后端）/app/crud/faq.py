from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.faq import FAQ
from app.schemas.faq import FAQCreate


class CRUDFAQ(CRUDBase[FAQ, FAQCreate]):
    def list_active(self, db: Session, category: Optional[str] = None) -> List[FAQ]:
        """获取启用的FAQ列表"""
        query = db.query(FAQ).filter(FAQ.status == 1)
        if category:
            query = query.filter(FAQ.category == category)
        return query.order_by(FAQ.sort_order.asc(), FAQ.faq_id.desc()).all()
    
    def increment_view(self, db: Session, faq_id: int):
        """增加查看次数"""
        faq = self.get(db, faq_id)
        if faq:
            faq.view_count = (faq.view_count or 0) + 1
            db.commit()


faq = CRUDFAQ(FAQ)

