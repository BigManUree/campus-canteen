from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload

from app.crud.base import CRUDBase
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate


class CRUDOrder(CRUDBase[Order, OrderCreate]):
    def list_by_user(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        order_status: Optional[int] = None,
        pay_status: Optional[int] = None,
    ) -> tuple[List[Order], int]:
        """获取用户订单列表，支持分页、状态与关键词搜索"""
        query = db.query(Order).options(
            joinedload(Order.canteen),
            joinedload(Order.items)
        ).filter(Order.user_id == user_id)

        if order_status is not None:
            query = query.filter(Order.order_status == order_status)

        if pay_status is not None:
            query = query.filter(Order.pay_status == pay_status)

        if keyword:
            keyword = keyword.strip()
            if keyword:
                query = query.filter(
                    or_(
                        Order.order_no.like(f"%{keyword}%"),
                        Order.pickup_code.like(f"%{keyword}%"),
                        Order.items.any(OrderItem.dish_name.like(f"%{keyword}%"))
                    )
                )

        total = query.count()
        offset = (page - 1) * page_size
        orders = query.order_by(Order.order_id.desc()).offset(offset).limit(page_size).all()
        return orders, total

    def list_admin(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        canteen_id: Optional[int] = None,
        order_status: Optional[int] = None,
        pay_status: Optional[int] = None,
        keyword: Optional[str] = None
    ) -> tuple[List[Order], int]:
        """管理端订单列表（支持筛选、分页），自动加载档口信息"""
        query = db.query(Order).options(
            joinedload(Order.canteen)
        )
        
        if canteen_id:
            query = query.filter(Order.canteen_id == canteen_id)
        
        if order_status is not None:
            query = query.filter(Order.order_status == order_status)
        
        if pay_status is not None:
            query = query.filter(Order.pay_status == pay_status)
        
        if keyword:
            query = query.filter(
                or_(
                    Order.order_no.like(f"%{keyword}%"),
                    Order.pickup_code.like(f"%{keyword}%")
                )
            )
        
        total = query.count()
        offset = (page - 1) * page_size
        orders = query.order_by(Order.order_id.desc()).offset(offset).limit(page_size).all()
        
        return orders, total

    def create_with_items(self, db: Session, user_id: int, obj_in: OrderCreate, total: float, discount_amount: float, pay_amount: float, pickup_code: str, items_payload: list[dict]) -> Order:
        """创建订单并自动加载档口信息"""
        order_no = datetime.utcnow().strftime("OC%Y%m%d%H%M%S%f")
        db_obj = Order(
            order_no=order_no,
            user_id=user_id,
            canteen_id=obj_in.canteen_id,
            order_type=obj_in.order_type,
            total_amount=total,
            discount_amount=discount_amount,
            pay_amount=pay_amount,
            pay_status=0,  # 默认未支付，需要通过支付接口完成支付
            pickup_code=pickup_code,
            pickup_time=obj_in.pickup_time,
            delivery_address=obj_in.delivery_address,
            delivery_latitude=obj_in.delivery_latitude,
            delivery_longitude=obj_in.delivery_longitude,
            remark=obj_in.remark,
        )
        db.add(db_obj)
        db.flush()
        items = []
        for item in items_payload:
            oi = OrderItem(
                order_id=db_obj.order_id,
                dish_id=item["dish_id"],
                dish_name=item["dish_name"],
                price=item["price"],
                quantity=item["quantity"],
                remark=item.get("remark"),
            )
            items.append(oi)
        db.add_all(items)
        db.commit()
        
        # 重新查询以加载关系
        db_obj = db.query(Order).options(
            joinedload(Order.canteen)
        ).filter(Order.order_id == db_obj.order_id).first()
        
        return db_obj


    def update_status(self, db: Session, order_id: int, order_status: int) -> Optional[Order]:
        """更新订单状态，并自动更新对应的时间字段，返回时加载档口信息"""
        from datetime import datetime
        
        update_data = {"order_status": order_status}
        
        # 根据状态自动更新对应的时间字段
        if order_status == 1:  # 制作中（商家接单）
            update_data["accept_time"] = datetime.now()
        elif order_status == 2:  # 待取餐（制作完成）
            update_data["ready_time"] = datetime.now()
        elif order_status == 4:  # 已完成
            if not self.get(db, order_id).complete_time:
                update_data["complete_time"] = datetime.now()
        elif order_status == 5:  # 已取消
            if not self.get(db, order_id).cancel_time:
                update_data["cancel_time"] = datetime.now()
        
        result = self.update_by_dict(db, order_id, update_data)
        
        # 重新查询以加载档口信息
        if result:
            result = db.query(Order).options(
                joinedload(Order.canteen)
            ).filter(Order.order_id == order_id).first()
        
        return result
    
    def update_pay_status(self, db: Session, order_id: int, pay_status: int) -> Optional[Order]:
        """更新支付状态"""
        return self.update_by_dict(db, order_id, {"pay_status": pay_status})
    
    def update_status_and_pay_status(self, db: Session, order_id: int, order_status: Optional[int] = None, pay_status: Optional[int] = None) -> Optional[Order]:
        """同时更新订单状态和支付状态"""
        update_data = {}
        if order_status is not None:
            update_data["order_status"] = order_status
        if pay_status is not None:
            update_data["pay_status"] = pay_status
        if update_data:
            return self.update_by_dict(db, order_id, update_data)
        return self.get(db, order_id)


order = CRUDOrder(Order)

