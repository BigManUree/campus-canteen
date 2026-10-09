"""
WebSocket 实时通知接口
用于订单状态实时推送
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set
from sqlalchemy.orm import Session
import json
from datetime import datetime

from app.api import deps
from app.core.logging import logger

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 存储所有活跃连接：{user_id: Set[WebSocket]}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # 存储管理员连接
        self.admin_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, user_id: int, is_admin: bool = False):
        """建立连接"""
        await websocket.accept()
        
        # 添加到用户连接列表
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # 如果是管理员，添加到管理员连接列表
        if is_admin:
            self.admin_connections.add(websocket)
        
        logger.info(f"WebSocket 连接建立: user_id={user_id}, is_admin={is_admin}, 当前连接数={len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """断开连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # 从管理员连接中移除
        self.admin_connections.discard(websocket)
        
        logger.info(f"WebSocket 连接断开: user_id={user_id}, 剩余连接数={len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """发送消息给指定用户"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"发送消息失败: user_id={user_id}, error={str(e)}")
                    disconnected.add(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)
    
    async def broadcast_to_admins(self, message: dict):
        """广播消息给所有管理员"""
        disconnected = set()
        for connection in self.admin_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息给管理员失败: error={str(e)}")
                disconnected.add(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.admin_connections.discard(conn)
        
        logger.info(f"广播消息给 {len(self.admin_connections)} 个管理员")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    def get_connection_count(self) -> dict:
        """获取连接统计"""
        return {
            "total_users": len(self.active_connections),
            "total_connections": sum(len(conns) for conns in self.active_connections.values()),
            "admin_connections": len(self.admin_connections)
        }


# 创建全局连接管理器
manager = ConnectionManager()


@router.websocket("/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token")
):

    user_id = None  # 初始化 user_id
    
    try:
        # 验证 token 并获取用户信息
        from app.core.security import decode_token
        from app.crud import user as user_crud
        from app.db.session import SessionLocal
        
        try:
            payload = decode_token(token)
            # JWT token 中用户ID存储在 sub 字段
            user_id = payload.get("sub")
            
            # 如果 user_id 是字符串，转换为整数
            if user_id and isinstance(user_id, str):
                user_id = int(user_id)
            
            if not user_id:
                await websocket.close(code=1008, reason="Invalid token: missing user_id")
                return
            
            # 从数据库获取用户信息（包括角色）
            db = SessionLocal()
            try:
                user = user_crud.user.get(db, user_id)
                if not user:
                    await websocket.close(code=1008, reason="User not found")
                    return
                
                if user.status != 1:
                    await websocket.close(code=1008, reason="User is disabled")
                    return
                
                role = user.role
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Token 验证失败: {str(e)}")
            await websocket.close(code=1008, reason=f"Token verification failed: {str(e)}")
            return
        
        # 判断是否为管理员
        is_admin = role in ["admin", "merchant", "sys_admin", "canteen_admin"]
        
        # 建立连接
        await manager.connect(websocket, user_id, is_admin)
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket 连接成功",
            "user_id": user_id,
            "is_admin": is_admin,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持连接并接收消息
        while True:
            try:
                # 接收客户端消息（心跳包等）
                data = await websocket.receive_text()
                
                # 处理心跳包
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    # 处理其他消息
                    try:
                        message = json.loads(data)
                        logger.info(f"收到客户端消息: user_id={user_id}, message={message}")
                    except json.JSONDecodeError:
                        logger.warning(f"无法解析客户端消息: {data}")
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket 消息处理错误: {str(e)}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket 连接错误: {str(e)}")
    
    finally:
        # 断开连接（只有在 user_id 有效时才断开）
        if user_id is not None:
            manager.disconnect(websocket, user_id)


@router.get("/stats")
async def get_websocket_stats(current=Depends(deps.require_admin)):
    """获取 WebSocket 连接统计（管理员）"""
    return manager.get_connection_count()


# ==================== 消息推送函数 ====================

async def notify_new_order(order_id: int, order_no: str, user_name: str, amount: float, canteen_name: str):
    """
    通知管理员有新订单
    
    在订单支付成功后调用此函数
    """
    message = {
        "type": "new_order",
        "title": "新订单提醒",
        "message": f"用户 {user_name} 下单成功",
        "order_id": order_id,
        "order_no": order_no,
        "amount": amount,
        "canteen_name": canteen_name,
        "timestamp": datetime.now().isoformat(),
        "sound": True  # 提示前端播放提示音
    }
    
    await manager.broadcast_to_admins(message)
    logger.info(f"已推送新订单通知: order_id={order_id}, order_no={order_no}")


async def notify_order_status_update(user_id: int, order_id: int, order_no: str, status: int, status_name: str):
    """
    通知用户订单状态更新
    
    在订单状态变更时调用此函数
    """
    message = {
        "type": "order_status_update",
        "title": "订单状态更新",
        "message": f"您的订单（{order_no}）{status_name}",
        "order_id": order_id,
        "order_no": order_no,
        "status": status,
        "status_name": status_name,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.send_personal_message(message, user_id)
    logger.info(f"已推送订单状态更新: user_id={user_id}, order_id={order_id}, status={status}")


async def notify_order_cancel(user_id: int, order_id: int, order_no: str, reason: str):
    """
    通知用户订单已取消
    """
    message = {
        "type": "order_cancelled",
        "title": "订单已取消",
        "message": f"您的订单（{order_no}）已取消",
        "order_id": order_id,
        "order_no": order_no,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.send_personal_message(message, user_id)
    logger.info(f"已推送订单取消通知: user_id={user_id}, order_id={order_id}")


async def notify_order_ready(user_id: int, order_id: int, order_no: str, pickup_code: str):
    """
    通知用户订单已制作完成，可以取餐
    """
    message = {
        "type": "order_ready",
        "title": "订单已完成",
        "message": f"您的订单（{order_no}）已制作完成，请凭取餐码取餐",
        "order_id": order_id,
        "order_no": order_no,
        "pickup_code": pickup_code,
        "timestamp": datetime.now().isoformat(),
        "sound": True
    }
    
    await manager.send_personal_message(message, user_id)
    logger.info(f"已推送订单完成通知: user_id={user_id}, order_id={order_id}")


async def notify_refund_request(refund_id: int, order_id: int, order_no: str, user_name: str, refund_amount: float, reason: str):
    """
    通知管理员有新的退款申请
    
    在用户申请退款后调用此函数
    """
    message = {
        "type": "refund_request",
        "title": "退款申请提醒",
        "message": f"用户 {user_name} 申请退款",
        "refund_id": refund_id,
        "order_id": order_id,
        "order_no": order_no,
        "user_name": user_name,
        "refund_amount": refund_amount,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        "sound": True  # 提示前端播放提示音
    }
    
    await manager.broadcast_to_admins(message)
    logger.info(f"已推送退款申请通知: refund_id={refund_id}, order_no={order_no}")


async def notify_refund_result(user_id: int, order_id: int, order_no: str, status: str, admin_remark: str = None):
    """
    通知用户退款审批结果
    
    在管理员处理退款申请后调用此函数
    """
    status_text = {
        "approved": "已批准",
        "rejected": "已拒绝",
        "completed": "已完成"
    }.get(status, status)
    
    message = {
        "type": "refund_result",
        "title": "退款审批结果",
        "message": f"您的退款申请（订单{order_no}）{status_text}",
        "order_id": order_id,
        "order_no": order_no,
        "status": status,
        "status_text": status_text,
        "admin_remark": admin_remark,
        "timestamp": datetime.now().isoformat(),
        "sound": True
    }
    
    await manager.send_personal_message(message, user_id)
    logger.info(f"已推送退款审批结果: user_id={user_id}, order_id={order_id}, status={status}")


async def broadcast_system_message(title: str, message: str):
    """
    广播系统消息给所有在线用户
    """
    msg = {
        "type": "system_message",
        "title": title,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast(msg)
    logger.info(f"已广播系统消息: {title}")


async def notify_pickup_timeout(order_id: int, order_no: str, user_id: int, timeout_hours: int):
    """
    通知用户取餐超时提醒
    
    在订单制作完成超过指定时间后调用此函数
    """
    message = {
        "type": "pickup_timeout",
        "title": "取餐提醒",
        "message": f"您的订单（{order_no}）已制作完成超过{timeout_hours}小时，请尽快取餐",
        "order_id": order_id,
        "order_no": order_no,
        "timeout_hours": timeout_hours,
        "timestamp": datetime.now().isoformat(),
        "sound": True
    }
    
    await manager.send_personal_message(message, user_id)
    logger.info(f"已推送取餐超时提醒: user_id={user_id}, order_id={order_id}, timeout={timeout_hours}小时")


