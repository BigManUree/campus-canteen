"""
库存管理服务
实现库存预扣、释放、扣减等功能
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List, Dict
from app.core.logging import logger
from app.models.dish import Dish
from app.models.order import Order, OrderItem


class InventoryLock:
    """库存锁定记录（存储在订单项的备注中）"""
    pass


def lock_inventory(db: Session, order_id: int, items: List[Dict]) -> bool:
    """预扣库存（下单时锁定）
    
    Args:
        db: 数据库会话
        order_id: 订单ID
        items: 订单项列表 [{"dish_id": 1, "quantity": 2}, ...]
    
    Returns:
        bool: 是否成功锁定
    """
    try:
        for item in items:
            dish_id = item["dish_id"]
            quantity = item["quantity"]
            
            # 获取菜品
            dish = db.query(Dish).filter(Dish.dish_id == dish_id).with_for_update().first()
            
            if not dish:
                logger.error(f"❌ 菜品不存在: dish_id={dish_id}")
                return False
            
            # 检查库存是否充足
            if dish.stock < quantity:
                logger.warning(f"⚠️ 库存不足: dish_id={dish_id}, 需要={quantity}, 剩余={dish.stock}")
                return False
            
            # 锁定库存（减少可用库存）
            dish.stock -= quantity
            logger.info(f"🔒 锁定库存: dish_id={dish_id}, dish_name={dish.name}, 数量={quantity}, 剩余库存={dish.stock}")
        
        db.commit()
        logger.info(f"✅ 订单 {order_id} 库存锁定成功")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 锁定库存失败 order_id={order_id}: {e}", exc_info=True)
        return False


def release_inventory(db: Session, order_id: int) -> bool:
    """释放库存（取消订单或支付超时）
    
    Args:
        db: 数据库会话
        order_id: 订单ID
    
    Returns:
        bool: 是否成功释放
    """
    try:
        # 获取订单项
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        
        if not order_items:
            logger.warning(f"⚠️ 订单 {order_id} 没有订单项")
            return True
        
        # 释放每个菜品的库存
        for item in order_items:
            dish = db.query(Dish).filter(Dish.dish_id == item.dish_id).with_for_update().first()
            
            if dish:
                # 恢复库存
                dish.stock += item.quantity
                logger.info(f"🔓 释放库存: dish_id={item.dish_id}, dish_name={item.dish_name}, 数量={item.quantity}, 恢复后库存={dish.stock}")
            else:
                logger.warning(f"⚠️ 菜品不存在，无法释放库存: dish_id={item.dish_id}")
        
        db.commit()
        logger.info(f"✅ 订单 {order_id} 库存释放成功")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 释放库存失败 order_id={order_id}: {e}", exc_info=True)
        return False


def deduct_inventory(db: Session, order_id: int) -> bool:
    """扣减库存（支付成功后真正扣减）
    
    注意：由于下单时已经锁定（减少）了库存，支付成功后不需要再次扣减
    这个函数主要用于记录日志和验证
    
    Args:
        db: 数据库会话
        order_id: 订单ID
    
    Returns:
        bool: 是否成功
    """
    try:
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        
        if not order_items:
            logger.warning(f"⚠️ 订单 {order_id} 没有订单项")
            return True
        
        # 验证库存状态
        for item in order_items:
            dish = db.query(Dish).filter(Dish.dish_id == item.dish_id).first()
            
            if dish:
                logger.info(f"✅ 库存已扣减: dish_id={item.dish_id}, dish_name={item.dish_name}, 当前库存={dish.stock}")
            else:
                logger.warning(f"⚠️ 菜品不存在: dish_id={item.dish_id}")
        
        logger.info(f"✅ 订单 {order_id} 库存扣减确认完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 扣减库存失败 order_id={order_id}: {e}", exc_info=True)
        return False


def check_and_release_expired_locks(db: Session, timeout_minutes: int = 30) -> int:
    """检查并释放超时未支付订单的库存锁定
    
    Args:
        db: 数据库会话
        timeout_minutes: 超时时间（分钟）
    
    Returns:
        int: 释放的订单数量
    """
    try:
        # 查找超时未支付的订单
        timeout_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        expired_orders = db.query(Order).filter(
            and_(
                Order.pay_status == 0,  # 未支付
                Order.order_status == 0,  # 待确认
                Order.create_time < timeout_time  # 超时
            )
        ).all()
        
        released_count = 0
        
        for order in expired_orders:
            # 释放库存
            if release_inventory(db, order.order_id):
                # 取消订单
                order.order_status = 5  # 已取消
                order.cancel_time = datetime.now()
                order.cancel_reason = "支付超时自动取消"
                db.commit()
                
                released_count += 1
                logger.info(f"✅ 订单 {order.order_id} ({order.order_no}) 支付超时，已自动取消并释放库存")
        
        if released_count > 0:
            logger.info(f"✅ 共释放 {released_count} 个超时订单的库存")
        
        return released_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 检查并释放超时库存失败: {e}", exc_info=True)
        return 0

