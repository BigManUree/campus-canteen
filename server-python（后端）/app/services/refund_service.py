"""
退款服务 - 处理退款审批、部分退款、自动批准等
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json

from app.models.refund import Refund
from app.models.order import Order, OrderItem
from app.models.dish import Dish
from app.services.notification_service import send_urgent_notification, send_normal_notification
import logging

logger = logging.getLogger(__name__)


class RefundService:
    """退款服务"""
    
    # 退款原因分类
    REASON_DONT_WANT = "dont_want"      # 不想要了
    REASON_TOO_LONG = "too_long"        # 等太久
    REASON_QUALITY = "quality"          # 质量问题
    REASON_OTHER = "other"              # 其他
    
    @staticmethod
    def create_refund(
        db: Session,
        order_id: int,
        user_id: int,
        reason: str,
        reason_category: str = REASON_OTHER,
        refund_items: Optional[List[Dict]] = None,
        refund_amount: Optional[Decimal] = None
    ) -> Refund:
        """
        创建退款申请
        
        Args:
            db: 数据库会话
            order_id: 订单ID
            user_id: 用户ID
            reason: 退款原因描述
            reason_category: 退款原因分类
            refund_items: 退款菜品列表（部分退款）[{"dish_id": 1, "quantity": 2, "amount": 30.0}]
            refund_amount: 退款金额（如果不提供则全额退款）
        """
        try:
            # 获取订单
            order = db.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                raise ValueError("订单不存在")
            
            if order.user_id != user_id:
                raise ValueError("无权操作此订单")
            
            # 检查是否已有待处理的退款申请
            existing_refund = db.query(Refund).filter(
                and_(
                    Refund.order_id == order_id,
                    Refund.status == "pending"
                )
            ).first()
            
            if existing_refund:
                raise ValueError("该订单已有待处理的退款申请")
            
            # 计算退款金额
            if refund_amount is None:
                if refund_items:
                    # 部分退款：计算选中菜品的金额
                    refund_amount = Decimal("0")
                    for item in refund_items:
                        refund_amount += Decimal(str(item["amount"]))
                else:
                    # 全额退款
                    refund_amount = Decimal(str(order.pay_amount))
            
            # 创建退款记录
            refund = Refund(
                order_id=order_id,
                user_id=user_id,
                refund_amount=float(refund_amount),
                reason=reason,
                reason_category=reason_category,
                refund_items=json.dumps(refund_items) if refund_items else None,
                status="pending",
                auto_approved=False
            )
            
            db.add(refund)
            db.commit()
            db.refresh(refund)
            
            logger.info(f"✅ 创建退款申请: refund_id={refund.refund_id}, order_id={order_id}, amount={refund_amount}, category={reason_category}")
            
            # 发送紧急通知给管理员
            # TODO: 获取管理员ID列表
            # await send_urgent_notification(
            #     db=db,
            #     user_id=admin_id,
            #     title="新退款申请",
            #     message=f"订单 {order.order_no} 申请退款 ¥{refund_amount}",
            #     category="refund",
            #     related_id=refund.refund_id
            # )
            
            return refund
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 创建退款申请失败: {e}")
            raise
    
    @staticmethod
    async def approve_refund(
        db: Session,
        refund_id: int,
        admin_id: int,
        admin_remark: Optional[str] = None,
        auto_approved: bool = False
    ) -> Refund:
        """
        批准退款
        
        Args:
            db: 数据库会话
            refund_id: 退款ID
            admin_id: 管理员ID
            admin_remark: 管理员备注
            auto_approved: 是否自动批准
        """
        try:
            # 获取退款记录
            refund = db.query(Refund).filter(Refund.refund_id == refund_id).first()
            if not refund:
                raise ValueError("退款记录不存在")
            
            if refund.status != "pending":
                raise ValueError(f"退款状态为 {refund.status}，不能批准")
            
            # 获取订单
            order = db.query(Order).filter(Order.order_id == refund.order_id).with_for_update().first()
            if not order:
                raise ValueError("订单不存在")
            
            # 更新退款状态
            refund.status = "approved"
            refund.approve_time = datetime.now()
            refund.admin_remark = admin_remark
            refund.auto_approved = auto_approved
            
            # 处理库存恢复
            if refund.refund_items:
                # 部分退款：恢复部分菜品库存
                refund_items = json.loads(refund.refund_items)
                for item in refund_items:
                    dish = db.query(Dish).filter(Dish.dish_id == item["dish_id"]).with_for_update().first()
                    if dish:
                        dish.stock += item["quantity"]
                        logger.info(f"🔓 恢复库存（部分退款）: dish_id={dish.dish_id}, quantity={item['quantity']}, new_stock={dish.stock}")
            else:
                # 全额退款：恢复所有菜品库存
                for item in order.items:
                    dish = db.query(Dish).filter(Dish.dish_id == item.dish_id).with_for_update().first()
                    if dish:
                        dish.stock += item.quantity
                        logger.info(f"🔓 恢复库存（全额退款）: dish_id={dish.dish_id}, quantity={item.quantity}, new_stock={dish.stock}")
            
            # 更新订单状态为已取消
            order.order_status = 5  # 已取消
            order.cancel_time = datetime.now()
            order.cancel_reason = f"退款批准：{refund.reason}"
            
            # 恢复优惠券（如果使用了）
            if order.discount_amount and order.discount_amount > 0:
                from app.models.coupon import UserCoupon
                user_coupon = db.query(UserCoupon).filter(
                    and_(
                        UserCoupon.used_order_id == order.order_id,
                        UserCoupon.status == 1
                    )
                ).first()
                
                if user_coupon:
                    user_coupon.status = 0
                    user_coupon.used_time = None
                    user_coupon.used_order_id = None
                    logger.info(f"🎫 恢复优惠券: coupon_id={user_coupon.coupon_id}")
            
            db.commit()
            db.refresh(refund)
            
            logger.info(f"✅ 退款批准成功: refund_id={refund_id}, auto_approved={auto_approved}")
            
            # 发送通知给用户
            await send_normal_notification(
                db=db,
                user_id=refund.user_id,
                title="退款已批准",
                message=f"您的退款申请已批准，退款金额 ¥{refund.refund_amount} 将在3-5个工作日内退回",
                category="refund",
                related_id=refund_id
            )
            
            return refund
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 批准退款失败: {e}")
            raise
    
    @staticmethod
    async def reject_refund(
        db: Session,
        refund_id: int,
        admin_id: int,
        admin_remark: str
    ) -> Refund:
        """拒绝退款"""
        try:
            refund = db.query(Refund).filter(Refund.refund_id == refund_id).first()
            if not refund:
                raise ValueError("退款记录不存在")
            
            if refund.status != "pending":
                raise ValueError(f"退款状态为 {refund.status}，不能拒绝")
            
            refund.status = "rejected"
            refund.approve_time = datetime.now()
            refund.admin_remark = admin_remark
            
            db.commit()
            db.refresh(refund)
            
            logger.info(f"✅ 退款拒绝: refund_id={refund_id}")
            
            # 发送通知给用户
            await send_normal_notification(
                db=db,
                user_id=refund.user_id,
                title="退款已拒绝",
                message=f"您的退款申请已被拒绝。原因：{admin_remark}",
                category="refund",
                related_id=refund_id
            )
            
            return refund
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 拒绝退款失败: {e}")
            raise
    
    @staticmethod
    async def check_pending_refunds(db: Session):
        """
        检查待处理的退款申请
        - 超过24小时提醒管理员
        - 超过3天自动批准
        """
        try:
            now = datetime.now()
            
            # 查询所有待处理的退款
            pending_refunds = db.query(Refund).filter(
                Refund.status == "pending"
            ).all()
            
            for refund in pending_refunds:
                hours_pending = (now - refund.create_time).total_seconds() / 3600
                
                # 超过3天（72小时）自动批准
                if hours_pending >= 72:
                    logger.warning(f"⚠️ 退款申请超过3天未处理，自动批准: refund_id={refund.refund_id}")
                    await RefundService.approve_refund(
                        db=db,
                        refund_id=refund.refund_id,
                        admin_id=0,  # 系统自动
                        admin_remark="超过3天未处理，系统自动批准（保护用户权益）",
                        auto_approved=True
                    )
                
                # 超过24小时提醒管理员
                elif hours_pending >= 24:
                    logger.warning(f"⚠️ 退款申请超过24小时未处理: refund_id={refund.refund_id}")
                    # TODO: 发送提醒给管理员
                    # await send_urgent_notification(
                    #     db=db,
                    #     user_id=admin_id,
                    #     title="退款申请超时提醒",
                    #     message=f"退款申请 #{refund.refund_id} 已超过24小时未处理",
                    #     category="refund",
                    #     related_id=refund.refund_id
                    # )
            
        except Exception as e:
            logger.error(f"❌ 检查待处理退款失败: {e}")
    
    @staticmethod
    def get_refund_statistics(db: Session, start_date: datetime, end_date: datetime) -> Dict:
        """
        获取退款统计数据
        
        Returns:
            {
                "total_count": 总退款数,
                "total_amount": 总退款金额,
                "by_category": {
                    "dont_want": {"count": 10, "amount": 500},
                    "too_long": {"count": 5, "amount": 200},
                    ...
                },
                "by_status": {
                    "pending": {"count": 3, "amount": 120},
                    "approved": {"count": 20, "amount": 800},
                    "rejected": {"count": 2, "amount": 50},
                    "completed": {"count": 1, "amount": 30}
                },
                "auto_approved_count": 自动批准数量
            }
        """
        try:
            refunds = db.query(Refund).filter(
                and_(
                    Refund.create_time >= start_date,
                    Refund.create_time <= end_date
                )
            ).all()
            
            stats = {
                "total_count": len(refunds),
                "total_amount": float(sum(float(r.refund_amount or 0) for r in refunds)),
                "by_category": {},
                "by_status": {
                    "pending": {"count": 0, "amount": 0.0},
                    "approved": {"count": 0, "amount": 0.0},
                    "rejected": {"count": 0, "amount": 0.0},
                    "completed": {"count": 0, "amount": 0.0},
                },
                "auto_approved_count": 0
            }
            
            # 按原因分类统计
            for refund in refunds:
                amount = float(refund.refund_amount or 0)
                category = refund.reason_category or "other"
                if category not in stats["by_category"]:
                    stats["by_category"][category] = {"count": 0, "amount": 0.0}
                
                stats["by_category"][category]["count"] += 1
                stats["by_category"][category]["amount"] += amount
                
                # 按状态统计
                status = refund.status or "pending"
                if status not in stats["by_status"]:
                    stats["by_status"][status] = {"count": 0, "amount": 0.0}
                stats["by_status"][status]["count"] += 1
                stats["by_status"][status]["amount"] += amount
                
                # 自动批准统计
                if refund.auto_approved:
                    stats["auto_approved_count"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ 获取退款统计失败: {e}")
            return {}
    
    @staticmethod
    def calculate_partial_refund_amount(
        db: Session,
        order_id: int,
        refund_items: List[Dict]
    ) -> Decimal:
        """
        计算部分退款金额
        
        Args:
            order_id: 订单ID
            refund_items: [{"dish_id": 1, "quantity": 2}]
        
        Returns:
            退款金额
        """
        try:
            order = db.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                raise ValueError("订单不存在")
            
            # 获取订单项
            order_items = {item.dish_id: item for item in order.items}
            
            refund_amount = Decimal("0")
            for refund_item in refund_items:
                dish_id = refund_item["dish_id"]
                quantity = refund_item["quantity"]
                
                if dish_id not in order_items:
                    raise ValueError(f"菜品 {dish_id} 不在订单中")
                
                order_item = order_items[dish_id]
                if quantity > order_item.quantity:
                    raise ValueError(f"退款数量 {quantity} 超过订单数量 {order_item.quantity}")
                
                # 计算该菜品的退款金额
                item_refund = Decimal(str(order_item.price)) * quantity
                refund_amount += item_refund
                
                # 添加金额到refund_items
                refund_item["amount"] = float(item_refund)
            
            # 如果使用了优惠券，按比例退款
            if order.discount_amount and order.discount_amount > 0:
                discount_ratio = Decimal(str(order.discount_amount)) / Decimal(str(order.total_amount))
                refund_amount = refund_amount * (1 - discount_ratio)
            
            return refund_amount
            
        except Exception as e:
            logger.error(f"❌ 计算部分退款金额失败: {e}")
            raise


# 便捷方法
async def create_full_refund(
    db: Session,
    order_id: int,
    user_id: int,
    reason: str,
    reason_category: str = RefundService.REASON_OTHER
) -> Refund:
    """创建全额退款申请"""
    return RefundService.create_refund(
        db=db,
        order_id=order_id,
        user_id=user_id,
        reason=reason,
        reason_category=reason_category,
        refund_items=None,
        refund_amount=None
    )


async def create_partial_refund(
    db: Session,
    order_id: int,
    user_id: int,
    reason: str,
    refund_items: List[Dict],
    reason_category: str = RefundService.REASON_OTHER
) -> Refund:
    """创建部分退款申请"""
    # 计算退款金额
    refund_amount = RefundService.calculate_partial_refund_amount(
        db=db,
        order_id=order_id,
        refund_items=refund_items
    )
    
    return RefundService.create_refund(
        db=db,
        order_id=order_id,
        user_id=user_id,
        reason=reason,
        reason_category=reason_category,
        refund_items=refund_items,
        refund_amount=refund_amount
    )

