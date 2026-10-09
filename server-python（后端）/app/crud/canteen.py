from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.crud.base import CRUDBase
from app.models.canteen import Canteen
from app.schemas.canteen import CanteenCreate, CanteenUpdate


class CRUDCanteen(CRUDBase[Canteen, CanteenCreate]):
    def get_by_name(self, db: Session, name: str) -> Optional[Canteen]:
        return db.query(Canteen).filter(Canteen.canteen_name == name).first()

    def list_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Canteen]:
        return db.query(Canteen).offset(skip).limit(limit).all()
    
    def update_status(self, db: Session, id: int, status: int) -> Optional[Canteen]:
        """更新食堂状态"""
        return self.update_by_dict(db, id, {"status": status})
    
    def delete_with_cascade(self, db: Session, canteen_id: int) -> bool:
        """级联删除食堂及其所有相关数据"""
        from app.models.queue import QueueInfo
        from app.models.dish import Dish
        from app.models.order import Order, OrderItem
        from app.models.canteen_review import CanteenReview
        from app.models.cart import CartItem
        from app.models.favorite import Favorite
        from app.models.refund import Refund
        from app.models.review import Review
        
        # 检查食堂是否存在
        canteen = self.get(db, canteen_id)
        if not canteen:
            return False
        
        try:
            # 1. 删除排队信息
            db.query(QueueInfo).filter(QueueInfo.canteen_id == canteen_id).delete(synchronize_session=False)
            
            # 2. 获取该食堂的所有订单ID和菜品ID
            order_ids = [order.order_id for order in db.query(Order.order_id).filter(Order.canteen_id == canteen_id).all()]
            dish_ids = [dish.dish_id for dish in db.query(Dish.dish_id).filter(Dish.canteen_id == canteen_id).all()]
            
            # 3. 删除食堂评价
            db.query(CanteenReview).filter(CanteenReview.canteen_id == canteen_id).delete(synchronize_session=False)
            
            if dish_ids:
                # 4. 删除菜品相关评价
                db.query(Review).filter(Review.dish_id.in_(dish_ids)).delete(synchronize_session=False)
                # 5. 删除购物车中的相关菜品
                db.query(CartItem).filter(CartItem.dish_id.in_(dish_ids)).delete(synchronize_session=False)
                # 6. 删除收藏中的相关菜品
                db.query(Favorite).filter(Favorite.dish_id.in_(dish_ids)).delete(synchronize_session=False)
                
            if order_ids:
                # 7. 删除退款记录
                db.query(Refund).filter(Refund.order_id.in_(order_ids)).delete(synchronize_session=False)
                # 8. 删除订单关联评价
                db.query(CanteenReview).filter(CanteenReview.order_id.in_(order_ids)).delete(synchronize_session=False)
                db.query(Review).filter(Review.order_id.in_(order_ids)).delete(synchronize_session=False)
                # 9. 删除订单项
                db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).delete(synchronize_session=False)
                # 10. 删除订单
                db.query(Order).filter(Order.order_id.in_(order_ids)).delete(synchronize_session=False)
            
            # 11. 删除该食堂的所有菜品
            db.query(Dish).filter(Dish.canteen_id == canteen_id).delete(synchronize_session=False)
            
            # 12. 最后删除食堂本身
            db.delete(canteen)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            raise e


canteen = CRUDCanteen(Canteen)

