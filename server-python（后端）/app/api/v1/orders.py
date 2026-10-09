from fastapi import APIRouter, Depends, HTTPException, Query, Body, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import Optional
from datetime import datetime, timedelta
import asyncio
import json

from app.api import deps
from app.api.decorators import handle_api_errors
from app.crud import order as order_crud
from app.crud import dish as dish_crud
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.canteen import Canteen
from app.models.refund import Refund
from app.models.review import Review
from app.models.message import Message
from app.models.order_status_log import OrderStatusLog
from app.schemas.order import (
    OrderCreate,
    OrderOut,
    OrderStatusUpdate,
    OrderMockPayRequest,
    OrderTimeline,
    TimelineEvent,
    OrderCancelRequest,
    OrderCancelResponse,
    OrderAdminListItem,
    OrderAdminListResponse,
    OrderAdminPageData,
    OrderAdminItemOut,
    OrderStatusSummaryOut,
    OrderStatusViewedIn,
)
from app.services import order_service
from app.services import notification_service
from app.api.v1.websocket import manager
from app.schemas.common import APIResponse, PageData
from app.utils.image import get_first_image_url
from app.utils.order_serializer import serialize_order, serialize_order_list

router = APIRouter(prefix="/order", tags=["order"])


def _build_order_items_payload(db: Session, order: Order):
    items = []
    for item in order.items or []:
        dish = dish_crud.dish.get(db, item.dish_id)
        items.append(
            OrderAdminItemOut(
                item_id=item.item_id,
                dish_id=item.dish_id,
                dish_name=item.dish_name,
                price=float(item.price or 0),
                quantity=item.quantity,
                remark=item.remark,
                image=get_first_image_url(dish.images) if dish else None,
            )
        )
    return items


ALLOWED_STATUS_TRANSITIONS = {
    0: [1, 5],
    1: [2, 5],
    2: [3, 4],
    3: [4],
    4: [],
    5: [],
}

ORDER_STATUS_NAMES = {
    0: "待确认",
    1: "制作中",
    2: "待取餐",
    3: "配送中",
    4: "已完成",
    5: "已取消",
}


def _run_async_task(coro):
    try:
        asyncio.run(coro)
    except Exception:
        pass


def _broadcast_admin_event(event_type: str, order: Order, message: str, extra: Optional[dict] = None):
    payload = {
        "type": event_type,
        "message": message,
        "order_id": order.order_id,
        "order_no": order.order_no,
        "canteen_id": order.canteen_id,
        "user_id": order.user_id,
        "pay_amount": float(order.pay_amount or 0),
        "order_status": order.order_status,
        "pay_status": order.pay_status,
        "timestamp": datetime.now().isoformat(),
        "sound": True,
    }
    if extra:
        payload.update(extra)
    _run_async_task(manager.broadcast_to_admins(payload))


def _broadcast_user_event(user_id: int, payload: dict):
    _run_async_task(manager.send_personal_message(payload, user_id))


def _get_order_status_time(order: Order, status_key: str):
    if status_key == "pending":
        return order.create_time if order.pay_status == 0 and order.order_status == 0 else None
    if status_key == "preparing":
        return order.accept_time or (order.update_time if order.order_status == 1 else None)
    if status_key == "ready":
        return order.ready_time or (order.update_time if order.order_status == 2 else None)
    if status_key == "delivering":
        return order.update_time if order.order_status == 3 else None
    return None


def _get_user_viewed_time(current: User, status_key: str):
    all_viewed_at = getattr(current, "order_viewed_all_at", None)
    status_viewed_at = getattr(current, f"order_viewed_{status_key}_at", None)
    if all_viewed_at and status_viewed_at:
        return max(all_viewed_at, status_viewed_at)
    return all_viewed_at or status_viewed_at


@router.post("/create", response_model=OrderOut)
@handle_api_errors("创建订单失败")
def create_order(payload: OrderCreate, current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    return order_service.create_order(db, current.user_id, payload)


@router.get("/list", response_model=list[OrderOut])
def list_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词，支持订单号、取餐码、菜品名称"),
    order_status: Optional[int] = Query(None, description="订单状态"),
    pay_status: Optional[int] = Query(None, description="支付状态"),
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    orders, _ = order_crud.order.list_by_user(
        db,
        current.user_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        order_status=order_status,
        pay_status=pay_status,
    )
    return serialize_order_list(orders, db)


@router.get("/status-summary", response_model=OrderStatusSummaryOut)
def get_order_status_summary(
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    def is_unviewed(status_key: str, status_time):
        viewed_time = _get_user_viewed_time(current, status_key)
        return bool(status_time and (viewed_time is None or status_time > viewed_time))

    orders, _ = order_crud.order.list_by_user(
        db,
        current.user_id,
        page=1,
        page_size=200,
    )

    summary = {
        "pending": 0,
        "preparing": 0,
        "ready": 0,
        "delivering": 0,
        "refund": 0,
    }

    refund_rows = (
        db.query(Refund.order_id, Refund.status, Refund.create_time)
        .filter(Refund.user_id == current.user_id)
        .all()
    )
    latest_refund_map = {}
    for order_id, status, create_time in refund_rows:
        if order_id is None or status != "pending":
            continue
        order_id = int(order_id)
        prev_time = latest_refund_map.get(order_id)
        if prev_time is None or (create_time and create_time > prev_time):
            latest_refund_map[order_id] = create_time

    for order in orders:
        pending_time = _get_order_status_time(order, "pending")
        if is_unviewed("pending", pending_time):
            summary["pending"] += 1

        preparing_time = _get_order_status_time(order, "preparing")
        if is_unviewed("preparing", preparing_time):
            summary["preparing"] += 1

        ready_time = _get_order_status_time(order, "ready")
        if is_unviewed("ready", ready_time):
            summary["ready"] += 1

        delivering_time = _get_order_status_time(order, "delivering")
        if is_unviewed("delivering", delivering_time):
            summary["delivering"] += 1

        refund_time = latest_refund_map.get(order.order_id)
        if is_unviewed("refund", refund_time):
            summary["refund"] += 1

    return OrderStatusSummaryOut(**summary)


@router.post("/status-viewed", response_model=OrderStatusSummaryOut)
def mark_order_status_viewed(
    payload: OrderStatusViewedIn,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    now = datetime.now()
    scope = payload.scope

    if scope == "all":
        current.order_viewed_all_at = now
        current.order_viewed_pending_at = now
        current.order_viewed_preparing_at = now
        current.order_viewed_ready_at = now
        current.order_viewed_delivering_at = now
        current.order_viewed_refund_at = now
    else:
        setattr(current, f"order_viewed_{scope}_at", now)

    db.add(current)
    db.commit()
    db.refresh(current)

    return get_order_status_summary(current=current, db=db)


@router.get("/admin/list", response_model=OrderAdminListResponse)
def admin_list_orders(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    orderNo: Optional[str] = Query(None, description="订单号"),
    userId: Optional[int] = Query(None, description="用户ID"),
    stallId: Optional[int] = Query(None, description="食堂ID"),
    status: Optional[int] = Query(None, description="订单状态"),
    paymentStatus: Optional[int] = Query(None, description="支付状态"),
    startTime: Optional[datetime] = Query(None, description="开始时间"),
    endTime: Optional[datetime] = Query(None, description="结束时间"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db),
):
    query = db.query(Order, User, Canteen).options(
        joinedload(Order.items)
    ).join(User, Order.user_id == User.user_id).join(Canteen, Order.canteen_id == Canteen.canteen_id)

    if deps.is_merchant_role(current.role):
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            return APIResponse.success(
                data=PageData.create(records=[], total=0, page_num=pageNum, page_size=pageSize)
            )
        query = query.filter(Order.canteen_id == merchant_canteen.canteen_id)

    if orderNo:
        query = query.filter(Order.order_no.like(f"%{orderNo}%"))
    if userId is not None:
        query = query.filter(Order.user_id == userId)
    if stallId is not None:
        query = query.filter(Order.canteen_id == stallId)
    if status is not None:
        query = query.filter(Order.order_status == status)
    if paymentStatus is not None:
        query = query.filter(Order.pay_status == paymentStatus)
    if startTime is not None:
        query = query.filter(Order.create_time >= startTime)
    if endTime is not None:
        query = query.filter(Order.create_time <= endTime)

    total = query.count()
    rows = query.order_by(Order.create_time.desc()).offset((pageNum - 1) * pageSize).limit(pageSize).all()

    records = [
        OrderAdminListItem(
            order_id=order.order_id,
            order_no=order.order_no,
            user_id=order.user_id,
            user_name=user.nickname or user.username,
            user_phone=user.phone,
            canteen_id=order.canteen_id,
            stall_name=canteen.canteen_name,
            order_type=order.order_type,
            pay_amount=float(order.pay_amount or 0),
            total_amount=float(order.total_amount or 0),
            pay_status=order.pay_status,
            order_status=order.order_status,
            create_time=order.create_time,
            pay_time=order.pay_time,
            complete_time=order.complete_time,
            items=_build_order_items_payload(db, order),
        )
        for order, user, canteen in rows
    ]

    page_data = OrderAdminPageData.create(records=records, total=total, page_num=pageNum, page_size=pageSize)

    return APIResponse.success(data=page_data)


@router.get("/detail/{order_id}", response_model=OrderOut)
def order_detail(order_id: int, current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    order = db.query(Order).options(
        joinedload(Order.items),
        joinedload(Order.canteen)
    ).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current.user_id and current.role not in ["merchant", "canteen_admin", "admin", "sys_admin"]:
        raise HTTPException(status_code=403, detail="无权访问此订单")
    return serialize_order(order, db)


@router.get("/timeline/{order_id}", response_model=OrderTimeline)
def get_order_timeline(order_id: int, current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    from app.models.order_status_log import OrderStatusLog
    
    order = order_crud.order.get(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order.user_id != current.user_id and current.role not in ["merchant", "canteen_admin", "admin", "sys_admin"]:
        raise HTTPException(status_code=403, detail="无权访问此订单")
    
    timeline_events = [
        TimelineEvent(
        status=0,
        status_name="订单创建",
        timestamp=order.create_time,
        description="用户下单成功",
            is_current=(order.order_status == 0 and order.pay_status == 0),
        )
    ]
    
    if order.pay_time:
        timeline_events.append(
            TimelineEvent(
            status=0,
            status_name="支付完成",
            timestamp=order.pay_time,
            description="订单已支付，等待商家确认",
                is_current=(order.order_status == 0 and order.pay_status == 1),
            )
        )
    
    if order.accept_time:
        timeline_events.append(
            TimelineEvent(
            status=1,
            status_name="商家接单",
            timestamp=order.accept_time,
            description="商家已接单，开始制作",
                is_current=(order.order_status == 1),
            )
        )
    
    if order.ready_time:
        timeline_events.append(
            TimelineEvent(
            status=2,
            status_name="制作完成",
            timestamp=order.ready_time,
            description="餐品已制作完成，等待取餐",
                is_current=(order.order_status == 2),
            )
        )
    
    if order.order_type == "delivery" and order.order_status >= 3:
        delivery_log = db.query(OrderStatusLog).filter(
            OrderStatusLog.order_id == order_id,
            OrderStatusLog.new_status == 3,
        ).first()
        if delivery_log:
            timeline_events.append(
                TimelineEvent(
                status=3,
                status_name="配送中",
                timestamp=delivery_log.create_time,
                operator_name=delivery_log.operator_name,
                description="订单配送中",
                    is_current=(order.order_status == 3),
                )
            )
    
    if order.complete_time:
        timeline_events.append(
            TimelineEvent(
            status=4,
            status_name="订单完成",
            timestamp=order.complete_time,
            description="订单已完成",
                is_current=(order.order_status == 4),
            )
        )
    
    if order.cancel_time:
        cancel_desc = "订单已取消"
        if order.cancel_reason:
            cancel_desc += f"，原因：{order.cancel_reason}"
        timeline_events.append(
            TimelineEvent(
            status=5,
            status_name="订单取消",
            timestamp=order.cancel_time,
            description=cancel_desc,
                is_current=(order.order_status == 5),
            )
        )
    
    status_logs = db.query(OrderStatusLog).filter(OrderStatusLog.order_id == order_id).order_by(OrderStatusLog.create_time).all()
    for log in status_logs:
        if log.new_status in [1, 3, 4, 5]:
            exists = any(
                e.status == log.new_status and abs((e.timestamp - log.create_time).total_seconds()) < 1
                for e in timeline_events
            )
            if not exists:
                timeline_events.append(
                    TimelineEvent(
                    status=log.new_status,
                    status_name=ORDER_STATUS_NAMES.get(log.new_status, f"状态{log.new_status}"),
                    timestamp=log.create_time,
                    operator_name=log.operator_name,
                    description=log.description or f"订单状态更新为{ORDER_STATUS_NAMES.get(log.new_status, '未知')}",
                        is_current=False,
                    )
                )
    
    timeline_events.sort(key=lambda x: x.timestamp)
    return OrderTimeline(
        order_id=order.order_id,
        order_no=order.order_no,
        current_status=order.order_status,
        current_status_name=ORDER_STATUS_NAMES.get(order.order_status, "未知"),
        timeline=timeline_events,
    )


@router.post("/pay/{order_id}", response_model=OrderOut)
def pay_order(
    order_id: int,
    payload: OrderMockPayRequest = Body(default=OrderMockPayRequest()),
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current.user_id:
        raise HTTPException(status_code=403, detail="无权支付此订单")
    if order.pay_status == 1:
        raise HTTPException(status_code=400, detail="订单已支付")
    if order.order_status == 5:
        raise HTTPException(status_code=400, detail="订单已取消，无法支付")
    if (order.pay_amount or 0) < 0:
        raise HTTPException(status_code=400, detail="支付金额异常")

    now = datetime.now()
    order.pay_status = payload.pay_status
    order.pay_time = now
    old_status = order.order_status
    order.order_status = payload.order_status
    if payload.order_status == 1 and not order.accept_time:
        order.accept_time = now
    db.commit()
    db.refresh(order)

    if payload.pay_status == 1:
        try:
            notification_service.send_order_status_notification(db, order)
        except Exception:
            pass

        _broadcast_user_event(order.user_id, {
            "type": "order_paid",
            "message": f"订单 {order.order_no} 支付成功",
            "order_id": order.order_id,
            "order_no": order.order_no,
            "pay_status": order.pay_status,
            "order_status": order.order_status,
            "pay_amount": float(order.pay_amount or 0),
            "timestamp": now.isoformat(),
        })

        _broadcast_admin_event(
            "new_paid_order",
            order,
            f"新支付订单 {order.order_no}，请及时处理",
            {"old_status": old_status}
        )

    return order


@router.put("/status/{order_id}", response_model=OrderOut)
def update_order_status(order_id: int, payload: OrderStatusUpdate, current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    if current.role not in ["merchant", "canteen_admin", "admin", "sys_admin"]:
        raise HTTPException(status_code=403, detail="需要商家或管理员权限")
    
    order = order_crud.order.get(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if deps.is_merchant_role(current.role):
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen or order.canteen_id != merchant_canteen.canteen_id:
            raise HTTPException(status_code=403, detail="无权操作其他档口的订单")

    old_status = order.order_status
    new_status = payload.order_status
    
    if order.order_status == 5:
        raise HTTPException(status_code=400, detail="已取消订单不允许变更状态")
    if order.pay_status == 0 and new_status not in [5]:
        raise HTTPException(status_code=400, detail="未支付订单仅允许取消")
    if db.query(Refund).filter(Refund.order_id == order_id, Refund.status.in_(["pending", "approved", "completed"])).first() and new_status != 5:
        raise HTTPException(status_code=400, detail="订单存在退款流程，不能更新为正常履约状态")

    if new_status not in ALLOWED_STATUS_TRANSITIONS.get(old_status, []):
        old_status_name = ORDER_STATUS_NAMES.get(old_status, str(old_status))
        new_status_name = ORDER_STATUS_NAMES.get(new_status, str(new_status))
        allowed_statuses = [ORDER_STATUS_NAMES.get(s, str(s)) for s in ALLOWED_STATUS_TRANSITIONS.get(old_status, [])]
        if not allowed_statuses:
            raise HTTPException(status_code=400, detail=f"订单状态为'{old_status_name}'时不允许再修改状态")
        raise HTTPException(status_code=400, detail=f"不允许从'{old_status_name}'转换到'{new_status_name}'，允许的状态：{', '.join(allowed_statuses)}")
    
    order = order_crud.order.update_status(db, order_id, new_status)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if old_status != new_status:
        try:
            notification_service.send_order_status_notification(db, order)
        except Exception:
            pass

        status_name = ORDER_STATUS_NAMES.get(new_status, f"状态{new_status}")
        _broadcast_user_event(order.user_id, {
            "type": "order_status_update",
            "message": f"您的订单（{order.order_no}）{status_name}",
            "order_id": order.order_id,
            "order_no": order.order_no,
            "status": new_status,
            "status_name": status_name,
            "timestamp": datetime.now().isoformat(),
        })

        admin_event_type = None
        admin_message = None
        if new_status == 1:
            admin_event_type = "order_accepted"
            admin_message = f"订单 {order.order_no} 已接单，正在制作中"
        elif new_status == 2:
            admin_event_type = "order_ready_for_pickup"
            admin_message = f"订单 {order.order_no} 已制作完成"

        if admin_event_type and admin_message:
            extra = {"old_status": old_status, "new_status": new_status}
            if new_status == 2:
                extra["pickup_code"] = order.pickup_code
            _broadcast_admin_event(admin_event_type, order, admin_message, extra)
    
    return order


@router.post("/cancel/{id}", response_model=OrderCancelResponse)
def cancel_order(
    id: int,
    payload: OrderCancelRequest = Body(...),
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    result = order_service.cancel_order(db, id, current, payload.cancel_reason or payload.reason)

    try:
        order = db.query(Order).filter(Order.order_id == id).first()
        if order:
            try:
                notification_service.send_order_status_notification(db, order)
            except Exception:
                pass

            cancel_message = order.cancel_reason and f"您的订单（{order.order_no}）已取消，原因：{payload.cancel_reason or payload.reason}"
            if order.pay_status == 1:
                cancel_message = f"您的订单（{order.order_no}）已取消，退款金额 ¥{float(order.pay_amount or 0)} 将原路退回，原因：{payload.cancel_reason or payload.reason}"
            else:
                cancel_message = f"您的订单（{order.order_no}）已取消，原因：{payload.cancel_reason or payload.reason}"
            if result.get("need_approval"):
                _broadcast_admin_event(
                    "refund_request_created",
                    order,
                    f"订单 {order.order_no} 提交了退款申请",
                    {
                        "refund_id": result.get("refund_id"),
                        "refund_amount": float(result.get("refund_amount") or 0),
                        "reason": payload.reason,
                    }
                )
                _broadcast_user_event(order.user_id, {
                    "type": "refund_request_created",
                    "message": f"您的订单（{order.order_no}）退款申请已提交，取消原因：{payload.cancel_reason or payload.reason}",
                    "order_id": order.order_id,
                    "order_no": order.order_no,
                    "refund_id": result.get("refund_id"),
                    "refund_amount": float(result.get("refund_amount") or 0),
                    "reason": payload.cancel_reason or payload.reason,
                    "timestamp": datetime.now().isoformat(),
                })
            else:
                _broadcast_user_event(order.user_id, {
                    "type": "order_cancelled",
                    "message": cancel_message,
                    "order_id": order.order_id,
                    "order_no": order.order_no,
                    "reason": payload.cancel_reason or payload.reason,
                    "timestamp": datetime.now().isoformat(),
                })
                _broadcast_admin_event(
                    "order_cancelled",
                    order,
                    f"订单 {order.order_no} 已取消，原因：{payload.cancel_reason or payload.reason}",
                    {"reason": payload.cancel_reason or payload.reason}
                )
        
    except Exception:
        pass

    return result


@router.delete("/delete/{order_id}", status_code=204)
def delete_order(
    order_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.user_id != current.user_id and current.role not in ["admin", "sys_admin"]:
        raise HTTPException(status_code=403, detail="无权删除此订单")

    db.query(OrderStatusLog).filter(OrderStatusLog.order_id == order_id).delete(synchronize_session=False)
    db.query(Message).filter(Message.order_id == order_id).delete(synchronize_session=False)
    db.query(Review).filter(Review.order_id == order_id).delete(synchronize_session=False)
    db.query(Refund).filter(Refund.order_id == order_id).delete(synchronize_session=False)
    db.query(OrderItem).filter(OrderItem.order_id == order_id).delete(synchronize_session=False)
    db.delete(order)
    db.commit()

    return Response(status_code=204)


@router.get("/verify/{pickup_code}", response_model=OrderOut)
def verify_pickup_code(
    pickup_code: str,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """管理员/商家核销取餐码"""
    if current.role not in ["merchant", "canteen_admin", "admin", "sys_admin"]:
        raise HTTPException(status_code=403, detail="需要商家或管理员权限")

    code = (pickup_code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="取餐码不能为空")

    order = db.query(Order).options(joinedload(Order.items)).filter(Order.pickup_code == code).first()
    if not order:
        raise HTTPException(status_code=404, detail="核销码无效，请重新输入")

    if deps.is_merchant_role(current.role):
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen or order.canteen_id != merchant_canteen.canteen_id:
            raise HTTPException(status_code=403, detail="无权核销其他食堂的订单")

    if order.pay_status != 1:
        raise HTTPException(status_code=400, detail="订单未支付，无法核销")

    if order.order_status == 5:
        raise HTTPException(status_code=400, detail="订单已取消，无法核销")

    if order.verify_time or order.order_status == 4:
        raise HTTPException(status_code=400, detail="该订单已核销，请勿重复操作")

    if order.order_status not in [2, 3]:
        raise HTTPException(status_code=400, detail="当前订单状态不允许核销")

    old_status = order.order_status
    now = datetime.now()
    order.verify_time = now
    order.pickup_time = now
    order.complete_time = now
    order.order_status = 4

    for item in order.items or []:
        dish = dish_crud.dish.get(db, item.dish_id)
        if dish:
            dish.sales = int(dish.sales or 0) + int(item.quantity or 0)

    db.add(OrderStatusLog(
        order_id=order.order_id,
        old_status=old_status,
        new_status=4,
        operator_id=current.user_id,
        operator_name=getattr(current, 'nickname', None) or getattr(current, 'username', None) or f"用户{current.user_id}",
        description=f"通过取餐码 {code} 完成核销",
    ))

    db.commit()
    db.refresh(order)

    try:
        notification_service.send_order_status_notification(db, order)
    except Exception:
        pass

    _broadcast_user_event(order.user_id, {
        "type": "order_verified",
        "message": f"您的订单（{order.order_no}）已完成核销",
        "order_id": order.order_id,
        "order_no": order.order_no,
        "timestamp": now.isoformat(),
    })

    return serialize_order(order, db)


@router.post("/confirm/{order_id}", response_model=OrderOut)
def confirm_order(
    order_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """用户确认取餐/收货，完成订单并累计菜品销量"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.user_id != current.user_id:
        raise HTTPException(status_code=403, detail="无权操作此订单")

    if order.pay_status != 1:
        raise HTTPException(status_code=400, detail="订单未支付，不能确认完成")

    if order.order_status == 5:
        raise HTTPException(status_code=400, detail="订单已取消，不能确认完成")

    if order.order_status == 4:
        return order

    if order.order_status not in [2, 3]:
        raise HTTPException(status_code=400, detail="当前订单状态不允许确认完成")

    old_status = order.order_status
    now = datetime.now()
    order.order_status = 4
    if not order.verify_time:
        order.verify_time = now
    if not order.complete_time:
        order.complete_time = now

    for item in order.items:
        dish = dish_crud.dish.get(db, item.dish_id)
        if dish:
            dish.sales = int(dish.sales or 0) + int(item.quantity or 0)

    db.add(OrderStatusLog(
        order_id=order.order_id,
        old_status=old_status,
        new_status=4,
        operator_id=current.user_id,
        operator_name=getattr(current, 'nickname', None) or getattr(current, 'username', None) or f"用户{current.user_id}",
        description="用户确认取餐，订单完成",
    ))

    db.commit()
    db.refresh(order)

    try:
        notification_service.send_order_status_notification(db, order)
    except Exception:
        pass

    return order


@router.post("/remind/{order_id}")
def remind_order(
    order_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """用户催单"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.user_id != current.user_id:
        raise HTTPException(status_code=403, detail="无权操作此订单")

    if order.pay_status != 1:
        raise HTTPException(status_code=400, detail="订单未支付，不能催单")

    if order.order_status != 1:
        raise HTTPException(status_code=400, detail="当前订单状态不能催单")

    try:
        notification_service.create_notification(
            db=db,
            user_id=current.user_id,
            title="催单成功",
            message=f"订单 {order.order_no} 已提醒商家尽快处理",
            notification_type="normal",
            category="order",
            related_id=order.order_id,
            priority=1,
        )
    except Exception:
        pass

    return {"success": True, "message": "催单成功"}
