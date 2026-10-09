"""
通知API - 处理通知的增删改查、已读状态等
"""
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from pydantic import BaseModel
from datetime import datetime

from app.api.deps import get_db, get_current_user, require_admin, require_merchant
from app.models.user import User
from app.models.notification import Notification
from app.services.notification_service import NotificationService
from app.schemas.common import APIResponse, PaginatedResponse, PageData

router = APIRouter()


CATEGORY_KEYS = ["refund", "order", "pickup", "promotion", "system"]


def ok(data, message: str = "success"):
    return APIResponse.success(data=data, message=message)


class NotificationResponse(BaseModel):
    notification_id: int
    title: str
    message: str
    notification_type: str
    category: str
    related_id: Optional[int]
    is_read: bool
    priority: int
    create_time: str
    read_time: Optional[str]
    
    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationPageResponse(PaginatedResponse[NotificationResponse]):
    pass


class NotificationCategoryStat(BaseModel):
    count: int
    unread: int


class NotificationStatisticsResponse(BaseModel):
    total: int
    unread: int
    read: int
    today: int
    categories: Dict[str, NotificationCategoryStat]


class MarkReadRequest(BaseModel):
    notification_ids: Optional[List[int]] = None  # None表示全部标记为已读


class DeleteNotificationsRequest(BaseModel):
    notification_ids: List[int]


class AdminSendNotificationRequest(BaseModel):
    user_ids: Optional[List[int]] = None
    role: Optional[str] = None
    title: str
    message: str
    notification_type: str = "normal"
    category: str = "system"
    related_id: Optional[int] = None
    priority: int = 0


class AdminTestNotificationRequest(BaseModel):
    user_id: Optional[int] = None
    title: str = "管理员测试通知"
    message: str = "这是一条管理员测试通知，用于验证通知中心是否正常工作。"


@router.get("/recent", response_model=List[NotificationResponse])
def get_recent_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    is_read: Optional[str] = Query(None, description="是否已读"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取最近通知列表（支持分页）"""
    # is_read 参数可能传来字符串 "null"，需要处理
    is_read_bool: Optional[bool] = None
    if is_read is not None and is_read.lower() not in ('null', 'none', ''):
        is_read_bool = is_read.lower() == 'true'

    offset = (page - 1) * page_size
    notifications = NotificationService.get_notifications(
        db=db,
        user_id=current_user.user_id,
        is_read=is_read_bool,
        limit=page_size,
        offset=offset
    )

    return [
        NotificationResponse(
            notification_id=n.notification_id,
            title=n.title,
            message=n.message,
            notification_type=n.notification_type,
            category=n.category,
            related_id=n.related_id,
            is_read=n.is_read,
            priority=n.priority,
            create_time=n.create_time.isoformat() if n.create_time else "",
            read_time=n.read_time.isoformat() if n.read_time else None
        )
        for n in notifications
    ]


@router.get("/list")
def get_notifications(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    readStatus: Optional[bool] = Query(None, description="是否已读（不传则返回全部）"),
    notification_type: Optional[str] = Query(None, description="通知类型：urgent/normal/marketing"),
    category: Optional[str] = Query(None, description="通知分类：refund/order/pickup/promotion"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取通知列表（统一后台分页格式）"""
    offset = (pageNum - 1) * pageSize
    notifications = NotificationService.get_notifications(
        db=db,
        user_id=current_user.user_id,
        is_read=readStatus,
        notification_type=notification_type,
        category=category,
        limit=pageSize,
        offset=offset
    )
    total = NotificationService.count_notifications(
        db=db,
        user_id=current_user.user_id,
        is_read=readStatus,
        notification_type=notification_type,
        category=category,
    )

    records = [
        NotificationResponse(
            notification_id=n.notification_id,
            title=n.title,
            message=n.message,
            notification_type=n.notification_type,
            category=n.category,
            related_id=n.related_id,
            is_read=n.is_read,
            priority=n.priority,
            create_time=n.create_time.isoformat() if n.create_time else "",
            read_time=n.read_time.isoformat() if n.read_time else None
        )
        for n in notifications
    ]

    return ok(PageData.create(records=records, total=total, page_num=pageNum, page_size=pageSize))


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取未读通知数量"""
    count = NotificationService.get_unread_count(db=db, user_id=current_user.user_id)
    return UnreadCountResponse(unread_count=count)


@router.get("/statistics")
def get_notification_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取通知统计"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    base_query = db.query(Notification).filter(
        Notification.user_id == current_user.user_id
    )

    totals = base_query.with_entities(
        func.count(Notification.notification_id).label("total"),
        func.sum(case((Notification.is_read == False, 1), else_=0)).label("unread"),  # noqa: E712
        func.sum(case((Notification.is_read == True, 1), else_=0)).label("read"),  # noqa: E712
        func.sum(case((Notification.create_time >= today, 1), else_=0)).label("today")
    ).one()

    category_rows = base_query.with_entities(
        Notification.category.label("category"),
        func.count(Notification.notification_id).label("count"),
        func.sum(case((Notification.is_read == False, 1), else_=0)).label("unread")  # noqa: E712
    ).group_by(Notification.category).all()

    categories = {
        key: {
            "count": 0,
            "unread": 0
        }
        for key in CATEGORY_KEYS
    }

    for row in category_rows:
        category_key = row.category or "system"
        categories[category_key] = {
            "count": int(row.count or 0),
            "unread": int(row.unread or 0)
        }

    return ok({
        "total": int(totals.total or 0),
        "unread": int(totals.unread or 0),
        "read": int(totals.read or 0),
        "today": int(totals.today or 0),
        "categories": categories
    })


@router.post("/mark-read")
def mark_as_read(
    request: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记通知为已读"""
    if request.notification_ids is None:
        # 标记全部为已读
        count = NotificationService.mark_all_as_read(db=db, user_id=current_user.user_id)
        return {"success": True, "message": f"已标记 {count} 条通知为已读"}
    else:
        # 标记指定通知为已读
        success_count = 0
        for notification_id in request.notification_ids:
            if NotificationService.mark_as_read(db=db, notification_id=notification_id, user_id=current_user.user_id):
                success_count += 1
        
        return {"success": True, "message": f"已标记 {success_count} 条通知为已读"}


@router.post("/batch-delete")
def batch_delete_notifications(
    request: DeleteNotificationsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量删除通知"""
    count = NotificationService.delete_notifications(
        db=db,
        user_id=current_user.user_id,
        notification_ids=request.notification_ids
    )
    return {"success": True, "message": f"已删除 {count} 条通知", "count": count}


@router.delete("/clear")
def clear_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空当前用户全部通知"""
    count = NotificationService.clear_notifications(
        db=db,
        user_id=current_user.user_id
    )
    return {"success": True, "message": f"已清空 {count} 条通知", "count": count}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除通知"""
    if not NotificationService.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.user_id
    ):
        raise HTTPException(status_code=404, detail="通知不存在")

    return {"success": True, "message": "通知已删除"}


@router.post("/send")
async def admin_send_notification(
    request: AdminSendNotificationRequest,
    current_user: User = Depends(require_merchant),
    db: Session = Depends(get_db)
):
    """管理端/商家端发送站内通知"""
    query = db.query(User).filter(User.status == 1)

    if request.user_ids:
        query = query.filter(User.user_id.in_(request.user_ids))
    elif request.role:
        query = query.filter(User.role == request.role)

    users = query.all()
    if not users:
        raise HTTPException(status_code=404, detail="未找到通知接收用户")

    created = []
    for user in users:
        notification = await NotificationService.create_notification(
            db=db,
            user_id=user.user_id,
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            category=request.category,
            related_id=request.related_id,
            priority=request.priority,
            push_immediately=True
        )
        created.append(notification.notification_id)

    return {
        "success": True,
        "message": f"通知发送成功，共发送 {len(created)} 人",
        "notification_ids": created
    }


@router.post("/send-test")
async def admin_send_test_notification(
    request: AdminTestNotificationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """给管理员本人或指定用户发送测试通知"""
    target_user_id = request.user_id or current_user.user_id
    notification = await NotificationService.create_notification(
        db=db,
        user_id=target_user_id,
        title=request.title,
        message=request.message,
        notification_type=NotificationService.TYPE_NORMAL,
        category=NotificationService.CATEGORY_SYSTEM,
        priority=1,
        push_immediately=True,
    )
    return ok({
        "notification_id": notification.notification_id,
        "user_id": target_user_id,
        "title": notification.title,
        "message": notification.message,
    }, message="测试通知发送成功")
