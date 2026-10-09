"""
通知服务 - 处理WebSocket消息持久化和推送
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.notification import Notification
from app.models.user import User
from app.models.canteen import Canteen
from app.api.v1.websocket import manager
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务"""

    # 通知类型
    TYPE_URGENT = "urgent"
    TYPE_NORMAL = "normal"
    TYPE_MARKETING = "marketing"

    # 通知分类
    CATEGORY_REFUND = "refund"
    CATEGORY_ORDER = "order"
    CATEGORY_PICKUP = "pickup"
    CATEGORY_PROMOTION = "promotion"
    CATEGORY_SYSTEM = "system"

    @staticmethod
    def get_admin_user_ids(db: Session) -> List[int]:
        """获取可接收管理通知的用户ID列表"""
        try:
            users = db.query(User).filter(
                User.role.in_(["admin", "merchant"]),
                User.status == 1
            ).all()
            return [user.user_id for user in users]
        except Exception as e:
            logger.error(f"❌ 获取管理员用户ID失败: {e}")
            return []

    @staticmethod
    def get_canteen_admin_user_ids(db: Session, canteen_id: Optional[int] = None) -> List[int]:
        """获取指定档口应接收通知的管理员/商家用户ID"""
        try:
            user_ids = set(NotificationService.get_admin_user_ids(db))
            if canteen_id is not None:
                canteen = db.query(Canteen).filter(Canteen.canteen_id == canteen_id).first()
                if canteen and canteen.merchant_user_id:
                    user_ids.add(canteen.merchant_user_id)
            return list(user_ids)
        except Exception as e:
            logger.error(f"❌ 获取档口管理员用户ID失败: {e}")
            return []

    @staticmethod
    async def notify_users(
        db: Session,
        user_ids: List[int],
        title: str,
        message: str,
        notification_type: str = "normal",
        category: str = "system",
        related_id: Optional[int] = None,
        priority: int = 0,
        push_immediately: bool = True
    ) -> List[Notification]:
        """批量给多个用户发送通知"""
        notifications: List[Notification] = []
        for user_id in list(dict.fromkeys(user_ids or [])):
            notification = await NotificationService.create_notification(
                db=db,
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                category=category,
                related_id=related_id,
                priority=priority,
                push_immediately=push_immediately,
            )
            notifications.append(notification)
        return notifications

    @staticmethod
    async def notify_admins(
        db: Session,
        title: str,
        message: str,
        category: str = "system",
        related_id: Optional[int] = None,
        priority: int = 1,
        canteen_id: Optional[int] = None,
        push_immediately: bool = True
    ) -> List[Notification]:
        """给管理员/商家发送通知"""
        admin_ids = NotificationService.get_canteen_admin_user_ids(db, canteen_id)
        if not admin_ids:
            logger.warning("⚠️ 没有可接收通知的管理员/商家用户")
            return []
        return await NotificationService.notify_users(
            db=db,
            user_ids=admin_ids,
            title=title,
            message=message,
            notification_type=NotificationService.TYPE_URGENT if priority >= 2 else NotificationService.TYPE_NORMAL,
            category=category,
            related_id=related_id,
            priority=priority,
            push_immediately=push_immediately,
        )

    @staticmethod
    async def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "normal",
        category: str = "system",
        related_id: Optional[int] = None,
        priority: int = 0,
        push_immediately: bool = True
    ) -> Notification:
        """
        创建通知

        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型（urgent/normal/marketing）
            category: 通知分类
            related_id: 关联ID
            priority: 优先级（0=普通, 1=重要, 2=紧急）
            push_immediately: 是否立即推送
        """
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                category=category,
                related_id=related_id,
                priority=priority,
                is_read=False,
                is_pushed=False
            )

            db.add(notification)
            db.commit()
            db.refresh(notification)

            logger.info(
                f"✅ 创建通知成功: user_id={user_id}, "
                f"type={notification_type}, category={category}"
            )

            if push_immediately:
                await NotificationService.push_notification(notification)

            return notification

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 创建通知失败: {e}")
            raise

    @staticmethod
    async def push_notification(notification: Notification):
        """推送通知到WebSocket"""
        try:
            message_data = {
                "notification_id": notification.notification_id,
                "title": notification.title,
                "message": notification.message,
                "type": notification.notification_type,
                "category": notification.category,
                "related_id": notification.related_id,
                "priority": notification.priority,
                "create_time": (
                    notification.create_time.isoformat()
                    if notification.create_time else None
                ),
                "is_read": notification.is_read
            }

            await manager.send_personal_message(
                message=message_data,
                user_id=notification.user_id
            )

            logger.info(
                f"✅ 推送通知成功: notification_id={notification.notification_id}"
            )

        except Exception as e:
            logger.error(f"❌ 推送通知失败: {e}")

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> bool:
        """标记通知为已读"""
        try:
            notification = db.query(Notification).filter(
                and_(
                    Notification.notification_id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()

            if not notification:
                return False

            notification.is_read = True
            notification.read_time = datetime.now()
            db.commit()

            logger.info(f"✅ 标记通知已读: notification_id={notification_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 标记通知已读失败: {e}")
            return False

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """标记用户所有通知为已读"""
        try:
            count = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False  # noqa: E712
                )
            ).update({
                "is_read": True,
                "read_time": datetime.now()
            })

            db.commit()
            logger.info(f"✅ 标记所有通知已读: user_id={user_id}, count={count}")
            return count

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 标记所有通知已读失败: {e}")
            return 0

    @staticmethod
    def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
        """删除单条通知"""
        try:
            notification = db.query(Notification).filter(
                and_(
                    Notification.notification_id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()

            if not notification:
                return False

            db.delete(notification)
            db.commit()
            logger.info(f"✅ 删除通知成功: notification_id={notification_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 删除通知失败: {e}")
            return False

    @staticmethod
    def delete_notifications(db: Session, user_id: int, notification_ids: List[int]) -> int:
        """批量删除通知"""
        try:
            ids = list(dict.fromkeys(notification_ids or []))
            if not ids:
                return 0

            count = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.notification_id.in_(ids)
            ).delete(synchronize_session=False)
            db.commit()
            logger.info(f"✅ 批量删除通知成功: user_id={user_id}, count={count}")
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 批量删除通知失败: {e}")
            return 0

    @staticmethod
    def clear_notifications(db: Session, user_id: int) -> int:
        """清空用户全部通知"""
        try:
            count = db.query(Notification).filter(
                Notification.user_id == user_id
            ).delete(synchronize_session=False)
            db.commit()
            logger.info(f"✅ 清空通知成功: user_id={user_id}, count={count}")
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 清空通知失败: {e}")
            return 0

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """获取未读通知数量"""
        try:
            count = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False  # noqa: E712
                )
            ).count()
            return count
        except Exception as e:
            logger.error(f"❌ 获取未读通知数量失败: {e}")
            return 0

    @staticmethod
    def get_notifications(
        db: Session,
        user_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        获取通知列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            is_read: 是否已读（None=全部）
            notification_type: 通知类型
            category: 通知分类
            limit: 每页数量
            offset: 偏移量
        """
        try:
            query = db.query(Notification).filter(
                Notification.user_id == user_id
            )

            if is_read is not None:
                query = query.filter(Notification.is_read == is_read)

            if notification_type:
                query = query.filter(
                    Notification.notification_type == notification_type
                )

            if category:
                query = query.filter(Notification.category == category)

            notifications = query.order_by(
                Notification.priority.desc(),
                Notification.create_time.desc()
            ).limit(limit).offset(offset).all()

            return notifications

        except Exception as e:
            logger.error(f"❌ 获取通知列表失败: {e}")
            return []

    @staticmethod
    async def get_unpushed_notifications(db: Session) -> List[Notification]:
        """获取未推送的通知（用于重连后补发）"""
        try:
            notifications = db.query(Notification).filter(
                Notification.is_pushed == False  # noqa: E712
            ).order_by(
                Notification.priority.desc(),
                Notification.create_time.asc()
            ).all()
            return notifications
        except Exception as e:
            logger.error(f"❌ 获取未推送通知失败: {e}")
            return []

    @staticmethod
    def count_notifications(
        db: Session,
        user_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> int:
        """获取通知总数（用于分页）"""
        try:
            query = db.query(Notification).filter(Notification.user_id == user_id)

            if is_read is not None:
                query = query.filter(Notification.is_read == is_read)

            if notification_type:
                query = query.filter(Notification.notification_type == notification_type)

            if category:
                query = query.filter(Notification.category == category)

            return query.count()
        except Exception as e:
            logger.error(f"❌ 获取通知总数失败: {e}")
            return 0

    @staticmethod
    def delete_old_notifications(db: Session, days: int = 30) -> int:
        """删除旧通知（已读且超过指定天数）"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            count = db.query(Notification).filter(
                and_(
                    Notification.is_read == True,  # noqa: E712
                    Notification.create_time < cutoff_date
                )
            ).delete()

            db.commit()
            logger.info(f"✅ 删除旧通知: count={count}")
            return count

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 删除旧通知失败: {e}")
            return 0


def send_order_status_notification(db: Session, order) -> None:
    """
    同步版：发送订单状态变更通知（持久化到数据库）

    在无法使用 async 的场景（如同步路由）中调用。
    实际 WebSocket 推送由前端轮询或 WebSocket 心跳触发。
    """
    try:
        STATUS_NAMES = {
            0: "待确认", 1: "制作中", 2: "待取餐",
            3: "配送中", 4: "已完成", 5: "已取消"
        }
        status_name = STATUS_NAMES.get(order.order_status, "状态更新")

        CATEGORY_MAP = {
            4: NotificationService.CATEGORY_PICKUP,
            5: NotificationService.CATEGORY_ORDER,
        }
        category = CATEGORY_MAP.get(
            order.order_status, NotificationService.CATEGORY_ORDER
        )

        priority = 2 if order.order_status in (2, 5) else 0

        notification = Notification(
            user_id=order.user_id,
            title=f"订单状态更新：{status_name}",
            message=f"您的订单（{order.order_no}）{status_name}",
            notification_type=(
                NotificationService.TYPE_URGENT
                if priority == 2 else NotificationService.TYPE_NORMAL
            ),
            category=category,
            related_id=order.order_id,
            priority=priority,
            is_read=False,
            is_pushed=False
        )
        db.add(notification)
        db.commit()
        logger.info(
            f"✅ 订单通知已持久化: order_id={order.order_id}, "
            f"status={order.order_status}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 持久化订单通知失败: {e}")


# ==================== 便捷异步方法 ====================

async def send_urgent_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    category: str = NotificationService.CATEGORY_SYSTEM,
    related_id: Optional[int] = None
):
    """发送紧急通知（播放声音）"""
    return await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=NotificationService.TYPE_URGENT,
        category=category,
        related_id=related_id,
        priority=2,
        push_immediately=True
    )


async def send_normal_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    category: str = NotificationService.CATEGORY_SYSTEM,
    related_id: Optional[int] = None
):
    """发送普通通知（静默推送）"""
    return await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=NotificationService.TYPE_NORMAL,
        category=category,
        related_id=related_id,
        priority=0,
        push_immediately=True
    )


async def send_marketing_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    related_id: Optional[int] = None
):
    """发送营销通知（可关闭）"""
    return await NotificationService.create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=NotificationService.TYPE_MARKETING,
        category=NotificationService.CATEGORY_PROMOTION,
        related_id=related_id,
        priority=0,
        push_immediately=True
    )
