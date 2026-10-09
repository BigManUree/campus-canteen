"""
消息通知服务
用于发送订单相关的消息通知
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.order import Order
from app.models.user import User
from app.models.canteen import Canteen
from app.core.logging import logger


class MessageService:
    """消息通知服务"""
    
    @staticmethod
    def send_order_notification_to_merchant(
        db: Session,
        order: Order,
        canteen: Canteen
    ) -> bool:
        """
        发送新订单通知给商家
        
        Args:
            db: 数据库会话
            order: 订单对象
            canteen: 档口对象
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 获取商家用户ID
            merchant_user_id = canteen.merchant_user_id
            
            # 如果档口没有关联商家，尝试获取所有档口管理员
            if not merchant_user_id:
                # 获取所有档口管理员
                admins = db.query(User).filter(
                    User.role == "canteen_admin",
                    User.status == 1
                ).all()
                
                if not admins:
                    logger.warning(f"档口 {canteen.canteen_id} 没有关联商家用户，且系统中无档口管理员")
                    return False
                
                # 给所有档口管理员发送通知
                for admin in admins:
                    _create_merchant_notification(db, order, admin.user_id)
                
                return True
            
            # 给指定商家发送通知
            return _create_merchant_notification(db, order, merchant_user_id)
            
        except Exception as e:
            logger.error(f"发送商家通知失败: {str(e)}", exc_info=True)
            db.rollback()
            return False
    
    @staticmethod
    def send_order_status_notification_to_user(
        db: Session,
        order: Order,
        status_text: str
    ) -> bool:
        """
        发送订单状态变更通知给用户
        
        Args:
            db: 数据库会话
            order: 订单对象
            status_text: 状态文本描述
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 获取系统管理员作为发送者
            system_user = db.query(User).filter(
                User.role.in_(["sys_admin", "canteen_admin"]),
                User.status == 1
            ).first()
            
            from_user_id = system_user.user_id if system_user else 1  # 默认使用ID=1
            
            # 构建消息内容
            message_title = "订单状态更新"
            message_content = f"您的订单（{order.order_no}）{status_text}。"
            
            # 如果是待取餐状态，添加取餐码
            if order.order_status == 2 and order.pickup_code:
                message_content += f"\n取餐码：{order.pickup_code}"
            
            # 创建消息记录
            message = Message(
                from_user_id=from_user_id,
                to_user_id=order.user_id,
                order_id=order.order_id,
                title=message_title,
                content=message_content,
                type=2,  # 系统消息
                message_type="order",
                is_read=0,
                create_time=datetime.now()
            )
            
            db.add(message)
            db.commit()
            
            logger.info(f"成功发送订单状态通知给用户 {order.user_id}，订单号：{order.order_no}")
            return True
            
        except Exception as e:
            logger.error(f"发送订单状态通知失败: {str(e)}", exc_info=True)
            db.rollback()
            return False


def _create_merchant_notification(db: Session, order: Order, merchant_user_id: int) -> bool:
    """
    创建商家通知消息
    
    Args:
        db: 数据库会话
        order: 订单对象
        merchant_user_id: 商家用户ID
        
    Returns:
        bool: 是否创建成功
    """
    try:
        # 构建消息内容
        message_title = "新订单提醒"
        message_content = f"您有新的订单（订单号：{order.order_no}），请及时处理。"
        
        # 添加订单金额信息
        message_content += f"\n订单金额：¥{order.pay_amount}"
        
        # 添加订单类型
        order_type_text = "自取" if order.order_type == "pickup" else "配送"
        message_content += f"\n订单类型：{order_type_text}"
        
        # 创建消息记录
        message = Message(
            from_user_id=order.user_id,  # 发送者是下单用户
            to_user_id=merchant_user_id,  # 接收者是商家
            order_id=order.order_id,
            title=message_title,
            content=message_content,
            type=2,  # 系统消息
            message_type="order",
            is_read=0,
            create_time=datetime.now()
        )
        
        db.add(message)
        db.commit()
        
        logger.info(f"成功发送订单通知给商家 {merchant_user_id}，订单号：{order.order_no}")
        return True
        
    except Exception as e:
        logger.error(f"创建商家通知失败: {str(e)}", exc_info=True)
        db.rollback()
        return False


# 可选：微信模板消息发送（需要配置微信服务号）
async def send_wechat_template_message(user_id: int, order: Order):
    """发送微信模板消息"""
    try:
        # 这里需要根据你的微信配置实现
        # 1. 获取用户的 openid
        # 2. 调用微信模板消息接口
        pass
    except Exception as e:
        logger.error(f"发送微信模板消息失败: {str(e)}")


# 可选：短信通知
async def send_sms_notification(phone: str, order: Order):
    """发送短信通知"""
    try:
        # 这里需要根据你的短信服务商实现
        # 例如：阿里云短信、腾讯云短信等
        pass
    except Exception as e:
        logger.error(f"发送短信通知失败: {str(e)}")


# 创建服务实例
message_service = MessageService()

