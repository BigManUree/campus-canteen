import random
import string
from decimal import Decimal
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import dish as dish_crud
from app.crud import order as order_crud
from app.crud import coupon as coupon_crud
from app.schemas.order import OrderCreate
from app.models.dish import Dish
from app.models.order import Order, OrderItem
from app.models.user import User
from app.services.notification_service import NotificationService


def _generate_pickup_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def create_order(db: Session, user_id: int, payload: OrderCreate):
    """
    创建订单（库存预扣版）
    - 下单时锁定库存（预扣）
    - 支付超时自动释放库存
    - 支付成功后库存已扣减（下单时已扣）
    - 统一事务管理，保证数据一致性
    """
    from app.core.logging import logger
    
    try:
        if not payload.items:
            raise HTTPException(status_code=400, detail="订单项不能为空")
        
        # 计算优惠金额
        discount_amount = Decimal("0")
        user_coupon_obj = None
        coupon_obj = None
        
        # 如果提供了优惠券ID，验证并计算优惠金额
        if payload.coupon_id:
            from app.models.coupon import UserCoupon, Coupon
            user_coupon_obj = db.query(UserCoupon).filter(
                UserCoupon.user_id == user_id,
                UserCoupon.coupon_id == payload.coupon_id,
                UserCoupon.status == 0
            ).first()
            
            if not user_coupon_obj:
                raise HTTPException(status_code=404, detail="优惠券不存在或已使用")
            
            coupon_obj = db.query(Coupon).filter(Coupon.coupon_id == payload.coupon_id).first()
            if not coupon_obj:
                raise HTTPException(status_code=404, detail="优惠券不存在")
            
            now = datetime.now()
            if now > user_coupon_obj.expire_time:
                raise HTTPException(status_code=400, detail="优惠券已过期")
        
        # 使用行锁查询菜品，防止并发超卖
        dish_ids = [i.dish_id for i in payload.items]
        dishes_list = db.query(Dish).filter(Dish.dish_id.in_(dish_ids)).with_for_update().all()
        dishes = {d.dish_id: d for d in dishes_list}
        
        # 验证菜品并计算总价
        total = Decimal("0")
        items_payload: list[dict] = []
        for item in payload.items:
            dish = dishes.get(item.dish_id)
            if not dish or dish.status != 1:
                raise HTTPException(status_code=404, detail=f"菜品 {item.dish_id} 不存在或已下架")
            if dish.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"菜品 {dish.name} 库存不足（剩余{dish.stock}份）")
            
            total += Decimal(dish.price) * item.quantity
            items_payload.append({
                "dish_id": dish.dish_id,
                "dish_name": dish.name,
                "price": float(dish.price),
                "quantity": item.quantity,
                "remark": item.remark,
            })
        
        # 计算优惠金额
        if coupon_obj:
            if total < coupon_obj.min_amount:
                raise HTTPException(status_code=400, detail=f"订单金额需满{float(coupon_obj.min_amount)}元")
            discount_amount = coupon_crud.coupon.calculate_discount(coupon_obj, total)
        
        pay_amount = total - discount_amount
        if pay_amount < 0:
            pay_amount = Decimal("0")
        
        # 🔒 库存预扣：下单时锁定库存
        logger.info(f"🔒 开始锁定库存: user_id={user_id}, 菜品数={len(payload.items)}")
        for item in payload.items:
            dish = dishes[item.dish_id]
            dish.stock -= item.quantity
            logger.info(f"🔒 锁定库存: dish_id={dish.dish_id}, dish_name={dish.name}, 数量={item.quantity}, 剩余={dish.stock}")
        
        # 生成取餐码（带去重检查）
        pickup_code = _generate_unique_pickup_code(db)
        
        # 创建订单（不自动提交）
        order_no = datetime.utcnow().strftime("OC%Y%m%d%H%M%S%f")
        order = Order(
            order_no=order_no,
            user_id=user_id,
            canteen_id=payload.canteen_id,
            order_type=payload.order_type,
            total_amount=float(total),
            discount_amount=float(discount_amount),
            pay_amount=float(pay_amount),
            pay_status=0,
            pickup_code=pickup_code,
            pickup_time=payload.pickup_time,
            delivery_address=payload.delivery_address,
            delivery_latitude=payload.delivery_latitude,
            delivery_longitude=payload.delivery_longitude,
            remark=payload.remark,
        )
        db.add(order)
        db.flush()  # 获取 order_id
        
        # 创建订单明细
        order_items = []
        for item_data in items_payload:
            order_item = OrderItem(
                order_id=order.order_id,
                dish_id=item_data["dish_id"],
                dish_name=item_data["dish_name"],
                price=item_data["price"],
                quantity=item_data["quantity"],
                remark=item_data.get("remark"),
            )
            order_items.append(order_item)
        db.add_all(order_items)
        
        # 如果使用了优惠券，标记为已使用
        if user_coupon_obj and discount_amount > 0:
            user_coupon_obj.status = 1
            user_coupon_obj.used_time = datetime.now()
            user_coupon_obj.used_order_id = order.order_id
            db.add(user_coupon_obj)
        
        # 统一提交事务
        db.commit()
        db.refresh(order)
        
        logger.info(f"✅ 订单创建成功: order_id={order.order_id}, order_no={order.order_no}, 库存已锁定")
        
        # 确保 items 关系被加载
        _ = order.items
        
        # 发送通知给商家（异步执行，不影响订单创建）
        try:
            awaitable = NotificationService.notify_admins(
                db=db,
                title="新订单提醒",
                message=f"收到新订单 {order.order_no}，金额 ¥{order.pay_amount}，请及时处理。",
                category=NotificationService.CATEGORY_ORDER,
                related_id=order.order_id,
                priority=2,
                canteen_id=payload.canteen_id,
            )
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(awaitable)
            except RuntimeError:
                asyncio.run(awaitable)
        except Exception as e:
            logger.error(f"发送站内管理通知失败: {str(e)}")

        # 发送通知给商家（异步执行，不影响订单创建）
        try:
            from app.services.message_service import message_service
            from app.models.canteen import Canteen
            
            # 获取档口信息
            canteen = db.query(Canteen).filter(Canteen.canteen_id == payload.canteen_id).first()
            if canteen:
                message_service.send_order_notification_to_merchant(
                    db=db,
                    order=order,
                    canteen=canteen
                )
        except Exception as e:
            # 通知发送失败不影响订单创建
            logger.error(f"发送商家通知失败: {str(e)}")
        
        return order
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        from app.core.logging import logger
        import traceback
        error_msg = f"创建订单失败: {str(e)}"
        error_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{error_trace}")
        raise HTTPException(status_code=500, detail=error_msg)


def _generate_unique_pickup_code(db: Session, max_attempts: int = 10) -> str:
    """生成唯一的取餐码，带去重检查"""
    for _ in range(max_attempts):
        code = "".join(random.choices(string.digits, k=6))
        # 检查是否已存在（只检查未完成的订单）
        exists = db.query(Order).filter(
            Order.pickup_code == code,
            Order.order_status.in_([0, 1, 2, 3])  # 待确认、制作中、待取餐、配送中
        ).first()
        if not exists:
            return code
    
    # 如果10次都重复，使用8位码
    return "".join(random.choices(string.digits, k=8))


def cancel_order(db: Session, order_id: int, current_user: User, reason: str) -> dict:
    """
    取消订单
    
    业务逻辑：
    1. 未支付订单：直接取消并恢复库存/优惠券
    2. 已支付订单：直接取消并自动完成退款，无需审核
    
    Args:
        db: 数据库会话
        current_user: 当前操作用户
        order_id: 订单ID
        reason: 取消原因
        
    Returns:
        dict: 包含取消结果或自动退款结果
        
    Raises:
        HTTPException: 订单不存在、无权操作、状态不允许取消等
    """
    from app.core.logging import logger
    
    try:
        operator_id = current_user.user_id
        operator_role = current_user.role
        operator_name = current_user.nickname or current_user.username or f"用户{operator_id}"

        # 1. 获取订单并验证
        order = db.query(Order).filter(Order.order_id == order_id).with_for_update().first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        # 验证取消权限
        if operator_role == "merchant":
            from app.models.canteen import Canteen
            merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == operator_id).first()
            if not merchant_canteen or order.canteen_id != merchant_canteen.canteen_id:
                raise HTTPException(status_code=403, detail="无权操作其他档口的订单")
        elif operator_role == "admin":
            pass
        elif order.user_id != operator_id:
            raise HTTPException(status_code=403, detail="无权操作此订单")
        
        # 验证订单状态是否可取消
        if order.order_status == 5:
            raise HTTPException(status_code=400, detail="订单已取消，不能重复取消")
        
        if order.order_status not in [0, 1]:
            status_names = {0: "待确认", 1: "制作中", 2: "待取餐", 3: "配送中", 4: "已完成", 5: "已取消"}
            current_status_name = status_names.get(order.order_status, "未知")
            raise HTTPException(
                status_code=400, 
                detail=f"订单状态为'{current_status_name}'，不允许取消。只能取消'待确认'或'制作中'的订单"
            )
        
        # 已支付订单：直接取消并自动退款
        refund_amount = float(order.pay_amount or 0)
        auto_refund_id = None
        if order.pay_status == 1:
            from app.models.refund import Refund

            existing_refund = db.query(Refund).filter(
                Refund.order_id == order_id,
                Refund.status.in_(["pending", "approved", "completed"])
            ).first()
            if existing_refund:
                raise HTTPException(status_code=400, detail="该订单已存在退款记录，请勿重复取消")

            refund = Refund(
                order_id=order_id,
                user_id=order.user_id,
                refund_amount=refund_amount,
                reason=reason,
                status="completed",
                admin_remark="订单详情页取消订单后自动退款",
                approve_time=datetime.now(),
                auto_approved=True
            )
            db.add(refund)
            db.flush()
            auto_refund_id = refund.refund_id
        logger.info(f"🔓 开始释放库存: order_id={order_id}")
        for item in order.items:
            dish = db.query(Dish).filter(Dish.dish_id == item.dish_id).with_for_update().first()
            if dish:
                dish.stock += item.quantity
                logger.info(f"🔓 释放库存: dish_id={dish.dish_id}, dish_name={dish.name}, 数量={item.quantity}, 恢复后={dish.stock}")
                db.add(dish)
        
        # 3. 如果使用了优惠券，恢复优惠券状态
        if order.discount_amount and order.discount_amount > 0:
            from app.models.coupon import UserCoupon
            user_coupon = db.query(UserCoupon).filter(
                UserCoupon.used_order_id == order_id,
                UserCoupon.status == 1  # 已使用
            ).first()
            
            if user_coupon:
                # 恢复为未使用状态
                user_coupon.status = 0
                user_coupon.used_time = None
                user_coupon.used_order_id = None
                db.add(user_coupon)
        
        from app.models.order_status_log import OrderStatusLog
        old_status = order.order_status
        order.order_status = 5  # 已取消
        order.cancel_time = datetime.now()
        order.cancel_reason = reason
        db.add(order)
        
        # 5. 记录状态变更日志
        role_label = "用户"
        if operator_role == "merchant":
            role_label = "商家"
        elif operator_role == "admin":
            role_label = "管理员"

        status_log = OrderStatusLog(
            order_id=order_id,
            old_status=old_status,
            new_status=5,
            operator_id=operator_id,
            operator_name=operator_name,
            description=f"{role_label}取消订单，原因：{reason}"
        )
        db.add(status_log)
        
        # 6. 提交事务
        db.commit()
        db.refresh(order)
        
        logger.info(f"✅ 订单取消成功: order_id={order_id}, 库存已释放")
        
        return {
            "success": True,
            "message": "订单已取消，退款将原路退回用户",
            "refund_amount": refund_amount if order.pay_status == 1 else None,
            "refund_id": auto_refund_id,
            "order_id": order.order_id,
            "order_status": order.order_status,
            "need_approval": False
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        from app.core.logging import logger
        import traceback
        error_msg = f"取消订单失败: {str(e)}"
        error_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{error_trace}")
        raise HTTPException(status_code=500, detail=error_msg)

