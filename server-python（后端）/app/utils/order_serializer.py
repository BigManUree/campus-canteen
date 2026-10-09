"""订单序列化工具

提供订单数据的序列化功能，自动包含档口信息和菜品图片
"""
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.canteen import Canteen
from app.models.dish import Dish
from app.models.review import Review
from app.utils.image import get_first_image_url


def serialize_order(order: Order, db: Session) -> Dict[str, Any]:
    """序列化订单，包含档口信息"""
    reviewed = db.query(Review.review_id).filter(Review.order_id == order.order_id).first() is not None

    canteen = None
    if order.canteen_id:
        if hasattr(order, 'canteen') and order.canteen:
            canteen = order.canteen
        else:
            canteen = db.query(Canteen).filter(
                Canteen.canteen_id == order.canteen_id
            ).first()
    
    canteen_info = None
    if canteen:
        canteen_info = {
            "canteen_id": canteen.canteen_id,
            "canteen_name": canteen.canteen_name,
            "building": canteen.building,
            "floor": canteen.floor,
            "window_no": canteen.window_no,
            "contact_phone": canteen.contact_phone
        }
    
    order_dict = {
        "order_id": order.order_id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "canteen_id": order.canteen_id,
        "canteen": canteen_info,
        "order_type": order.order_type,
        "total_amount": float(order.total_amount),
        "discount_amount": float(order.discount_amount),
        "pay_amount": float(order.pay_amount),
        "pay_status": order.pay_status,
        "pay_time": order.pay_time,
        "order_status": order.order_status,
        "pickup_code": order.pickup_code,
        "pickup_time": order.pickup_time,
        "verify_time": order.verify_time,
        "accept_time": order.accept_time,
        "ready_time": order.ready_time,
        "complete_time": order.complete_time,
        "cancel_time": order.cancel_time,
        "cancel_reason": order.cancel_reason,
        "delivery_address": order.delivery_address,
        "delivery_latitude": float(order.delivery_latitude) if order.delivery_latitude else None,
        "delivery_longitude": float(order.delivery_longitude) if order.delivery_longitude else None,
        "remark": order.remark,
        "create_time": order.create_time,
        "update_time": order.update_time,
        "is_reviewed": reviewed,
        "items": []
    }
    
    for item in order.items:
        dish = db.query(Dish).filter(Dish.dish_id == item.dish_id).first()
        image_url = get_first_image_url(dish.images) if dish else None
        
        order_dict["items"].append({
            "item_id": item.item_id,
            "dish_id": item.dish_id,
            "dish_name": item.dish_name,
            "price": float(item.price),
            "quantity": item.quantity,
            "remark": item.remark,
            "image": image_url
        })
    
    return order_dict


def serialize_order_list(orders: list[Order], db: Session) -> list[Dict[str, Any]]:
    """批量序列化订单列表"""
    order_ids = [order.order_id for order in orders if order.order_id]
    reviewed_order_ids = set()
    if order_ids:
        reviewed_order_ids = {
            row[0]
            for row in db.query(Review.order_id)
            .filter(Review.order_id.in_(order_ids))
            .distinct()
            .all()
        }

    canteen_ids = list(set(order.canteen_id for order in orders if order.canteen_id))
    canteens_dict = {}
    if canteen_ids:
        canteens = db.query(Canteen).filter(Canteen.canteen_id.in_(canteen_ids)).all()
        canteens_dict = {c.canteen_id: c for c in canteens}
    
    dish_ids = []
    for order in orders:
        for item in order.items:
            dish_ids.append(item.dish_id)
    dish_ids = list(set(dish_ids))
    
    dishes_dict = {}
    if dish_ids:
        dishes = db.query(Dish).filter(Dish.dish_id.in_(dish_ids)).all()
        dishes_dict = {d.dish_id: d for d in dishes}
    
    result = []
    for order in orders:
        canteen = None
        if order.canteen_id:
            if hasattr(order, 'canteen') and order.canteen:
                canteen = order.canteen
            else:
                canteen = canteens_dict.get(order.canteen_id)
        
        canteen_info = None
        if canteen:
            canteen_info = {
                "canteen_id": canteen.canteen_id,
                "canteen_name": canteen.canteen_name,
                "building": canteen.building,
                "floor": canteen.floor,
                "window_no": canteen.window_no,
                "contact_phone": canteen.contact_phone
            }
        
        order_dict = {
            "order_id": order.order_id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "canteen_id": order.canteen_id,
            "canteen": canteen_info,
            "order_type": order.order_type,
            "total_amount": float(order.total_amount),
            "discount_amount": float(order.discount_amount),
            "pay_amount": float(order.pay_amount),
            "pay_status": order.pay_status,
            "pay_time": order.pay_time,
            "order_status": order.order_status,
            "pickup_code": order.pickup_code,
            "pickup_time": order.pickup_time,
            "verify_time": order.verify_time,
            "accept_time": order.accept_time,
            "ready_time": order.ready_time,
            "complete_time": order.complete_time,
            "cancel_time": order.cancel_time,
            "cancel_reason": order.cancel_reason,
            "delivery_address": order.delivery_address,
            "delivery_latitude": float(order.delivery_latitude) if order.delivery_latitude else None,
            "delivery_longitude": float(order.delivery_longitude) if order.delivery_longitude else None,
            "remark": order.remark,
            "create_time": order.create_time,
            "update_time": order.update_time,
            "is_reviewed": order.order_id in reviewed_order_ids,
            "items": []
        }
        
        for item in order.items:
            dish = dishes_dict.get(item.dish_id)
            image_url = get_first_image_url(dish.images) if dish else None
            order_dict["items"].append({
                "item_id": item.item_id,
                "dish_id": item.dish_id,
                "dish_name": item.dish_name,
                "price": float(item.price),
                "quantity": item.quantity,
                "remark": item.remark,
                "image": image_url
            })
        
        result.append(order_dict)
    
    return result
