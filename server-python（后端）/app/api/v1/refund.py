"""
退款API - 处理退款申请、审批、统计等
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import asyncio
import json

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.refund import Refund
from app.models.order import Order
from app.models.canteen import Canteen
from app.api.v1.websocket import manager
from app.services.refund_service import RefundService, create_full_refund, create_partial_refund
from app.services.notification_service import NotificationService, send_normal_notification
from app.schemas.common import APIResponse, PageData
from app.schemas.refund import (
    RefundAdminListItem,
    RefundAdminListResponse,
    RefundDetailOut,
    RefundDetailResponse,
    RefundAuditRequest,
    RefundAuditResponse,
    RefundAuditResult,
    RefundItemOut,
)
from app.crud import dish as dish_crud
from app.utils.image import get_first_image_url

router = APIRouter()


def _build_refund_items_payload(db: Session, order: Optional[Order], refund: Refund):
    if not order:
        return []

    parsed_refund_items = None
    if refund.refund_items:
        try:
            parsed_refund_items = json.loads(refund.refund_items)
        except Exception:
            parsed_refund_items = None

    quantity_map = {}
    if isinstance(parsed_refund_items, list):
        for item in parsed_refund_items:
            if not isinstance(item, dict):
                continue
            dish_id = item.get("dish_id")
            if dish_id is None:
                continue
            quantity_map[int(dish_id)] = int(item.get("quantity") or item.get("count") or item.get("num") or 1)

    items = []
    for item in order.items or []:
        if quantity_map and item.dish_id not in quantity_map:
            continue
        dish = dish_crud.dish.get(db, item.dish_id)
        image_url = get_first_image_url(dish.images) if dish else None
        items.append(
            RefundItemOut(
                item_id=item.item_id,
                dish_id=item.dish_id,
                dish_name=item.dish_name,
                price=float(item.price or 0),
                quantity=quantity_map.get(item.dish_id, item.quantity),
                remark=item.remark,
                image=image_url,
                dish_image=image_url,
            )
        )
    return items


def _refund_async_task(coro):
    try:
        asyncio.run(coro)
    except Exception:
        pass


def _broadcast_admin_refund_event(event_type: str, order: Optional[Order], message: str, extra: Optional[dict] = None):
    payload = {
        "type": event_type,
        "message": message,
        "order_id": order.order_id if order else None,
        "order_no": order.order_no if order else None,
        "canteen_id": order.canteen_id if order else None,
        "user_id": order.user_id if order else None,
        "pay_amount": float(order.pay_amount or 0) if order else 0,
        "order_status": order.order_status if order else None,
        "pay_status": order.pay_status if order else None,
        "timestamp": datetime.now().isoformat(),
        "sound": True,
    }
    if extra:
        payload.update(extra)
    _refund_async_task(manager.broadcast_to_admins(payload))


class RefundItemRequest(BaseModel):
    dish_id: int
    quantity: int


class CreateRefundRequest(BaseModel):
    order_id: int
    reason: str
    reason_category: str = "other"
    refund_items: Optional[List[RefundItemRequest]] = None


class ApproveRefundRequest(BaseModel):
    admin_remark: Optional[str] = None


class RejectRefundRequest(BaseModel):
    admin_remark: str


class RefundResponse(BaseModel):
    refund_id: int
    order_id: int
    user_id: int
    refund_amount: float
    reason: str
    reason_category: Optional[str]
    refund_items: Optional[str]
    status: str
    admin_remark: Optional[str]
    approve_time: Optional[str]
    auto_approved: bool
    create_time: str

    class Config:
        from_attributes = True


def _check_merchant_refund_permission(current_user: User, refund_id: int, db: Session):
    refund_obj = db.query(Refund).filter(Refund.refund_id == refund_id).first()
    if not refund_obj:
        raise HTTPException(status_code=404, detail="退款记录不存在")
    order = db.query(Order).filter(Order.order_id == refund_obj.order_id).first()
    merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current_user.user_id).first()
    if not merchant_canteen or (order and order.canteen_id != merchant_canteen.canteen_id):
        raise HTTPException(status_code=403, detail="只能处理自己档口的退款申请")
    return refund_obj


@router.post("/create", response_model=RefundResponse)
async def create_refund(request: CreateRefundRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if request.refund_items:
            refund_items = [{"dish_id": item.dish_id, "quantity": item.quantity} for item in request.refund_items]
            refund = await create_partial_refund(
                db=db,
                order_id=request.order_id,
                user_id=current_user.user_id,
                reason=request.reason,
                refund_items=refund_items,
                reason_category=request.reason_category,
            )
        else:
            refund = await create_full_refund(
                db=db,
                order_id=request.order_id,
                user_id=current_user.user_id,
                reason=request.reason,
                reason_category=request.reason_category,
            )

        try:
            order = db.query(Order).filter(Order.order_id == refund.order_id).first()
            await NotificationService.notify_admins(
                db=db,
                title="新的退款申请",
                message=f"订单 {order.order_no if order else refund.order_id} 提交了退款申请，金额 ¥{refund.refund_amount}",
                category=NotificationService.CATEGORY_REFUND,
                related_id=refund.refund_id,
                priority=2,
                canteen_id=order.canteen_id if order else None,
            )
            _broadcast_admin_refund_event(
                "refund_request_created",
                order,
                f"订单 {order.order_no if order else refund.order_id} 提交了退款申请",
                {
                    "refund_id": refund.refund_id,
                    "refund_amount": float(refund.refund_amount or 0),
                    "reason": refund.reason,
                }
            )
        except Exception as notify_error:
            print(f"发送管理员退款通知失败: {notify_error}")

        return RefundResponse(
            refund_id=refund.refund_id,
            order_id=refund.order_id,
            user_id=refund.user_id,
            refund_amount=refund.refund_amount,
            reason=refund.reason,
            reason_category=refund.reason_category,
            refund_items=refund.refund_items,
            status=refund.status,
            admin_remark=refund.admin_remark,
            approve_time=refund.approve_time.isoformat() if refund.approve_time else None,
            auto_approved=refund.auto_approved,
            create_time=refund.create_time.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建退款申请失败: {str(e)}")


@router.get("/admin/list", response_model=RefundAdminListResponse)
def admin_list_refunds(
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    refundStatus: Optional[str] = Query(None),
    orderNo: Optional[str] = Query(None),
    userId: Optional[int] = Query(None),
    startTime: Optional[datetime] = Query(None),
    endTime: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("admin", "sys_admin", "merchant", "canteen_admin"):
        raise HTTPException(status_code=403, detail="需要管理员或商家权限")

    query = db.query(Refund, Order, User, Canteen).join(Order, Refund.order_id == Order.order_id).join(User, Refund.user_id == User.user_id).join(Canteen, Order.canteen_id == Canteen.canteen_id)

    if current_user.role in ("merchant", "canteen_admin"):
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current_user.user_id).first()
        if not merchant_canteen:
            return APIResponse.success(PageData.create(records=[], total=0, page_num=pageNum, page_size=pageSize))
        query = query.filter(Order.canteen_id == merchant_canteen.canteen_id)

    if refundStatus:
        query = query.filter(Refund.status == refundStatus)
    if orderNo:
        query = query.filter(Order.order_no.like(f"%{orderNo}%"))
    if userId is not None:
        query = query.filter(Refund.user_id == userId)
    if startTime is not None:
        query = query.filter(Refund.create_time >= startTime)
    if endTime is not None:
        query = query.filter(Refund.create_time <= endTime)

    total = query.count()
    rows = query.order_by(Refund.create_time.desc()).offset((pageNum - 1) * pageSize).limit(pageSize).all()

    records = []
    for refund, order, user, canteen in rows:
        order_items = _build_refund_items_payload(db, order, refund)
        records.append(
            RefundAdminListItem(
                refund_id=refund.refund_id,
                order_id=refund.order_id,
                order_no=order.order_no,
                user_id=refund.user_id,
                user_name=user.nickname or user.username,
                user_phone=user.phone,
                canteen_id=order.canteen_id,
                stall_name=canteen.canteen_name,
                refund_amount=float(refund.refund_amount or 0),
                reason=refund.reason,
                reason_category=refund.reason_category,
                refund_items=refund.refund_items,
                items=order_items,
                order_items=order_items,
                status=refund.status,
                admin_remark=refund.admin_remark,
                approve_time=refund.approve_time,
                auto_approved=bool(refund.auto_approved),
                create_time=refund.create_time,
            )
        )

    return APIResponse.success(
        PageData.create(records=records, total=total, page_num=pageNum, page_size=pageSize)
    )


@router.get("/admin/detail/{refund_id}", response_model=RefundDetailResponse)
def get_admin_refund_detail(refund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ("admin", "sys_admin", "merchant", "canteen_admin"):
        raise HTTPException(status_code=403, detail="需要管理员或商家权限")

    row = db.query(Refund, Order, User, Canteen).join(Order, Refund.order_id == Order.order_id).join(User, Refund.user_id == User.user_id).join(Canteen, Order.canteen_id == Canteen.canteen_id).filter(Refund.refund_id == refund_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="退款记录不存在")

    refund, order, user, canteen = row
    if current_user.role in ("merchant", "canteen_admin"):
        _check_merchant_refund_permission(current_user, refund_id, db)

    detail_items = _build_refund_items_payload(db, order, refund)
    return APIResponse.success(
        RefundDetailOut(
            refund_id=refund.refund_id,
            order_id=refund.order_id,
            order_no=order.order_no,
            user_id=refund.user_id,
            user_name=user.nickname or user.username,
            user_phone=user.phone,
            canteen_id=order.canteen_id,
            stall_name=canteen.canteen_name,
            refund_amount=float(refund.refund_amount or 0),
            reason=refund.reason,
            reason_category=refund.reason_category,
            refund_items=refund.refund_items,
            items=detail_items,
            order_items=detail_items,
            status=refund.status,
            admin_remark=refund.admin_remark,
            approve_time=refund.approve_time,
            auto_approved=bool(refund.auto_approved),
            create_time=refund.create_time,
            order_status=order.order_status,
            pay_status=order.pay_status,
            order_amount=float(order.pay_amount or 0),
            order_create_time=order.create_time,
        )
    )


@router.post("/admin/audit/{refund_id}", response_model=RefundAuditResponse)
async def audit_refund(refund_id: int, request: RefundAuditRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ("admin", "sys_admin", "merchant", "canteen_admin"):
        raise HTTPException(status_code=403, detail="需要管理员或商家权限")

    if current_user.role in ("merchant", "canteen_admin"):
        _check_merchant_refund_permission(current_user, refund_id, db)

    if request.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action 仅支持 approve 或 reject")

    try:
        if request.action == "approve":
            refund = await RefundService.approve_refund(
                db=db,
                refund_id=refund_id,
                admin_id=current_user.user_id,
                admin_remark=request.admin_remark,
                auto_approved=False,
            )
        else:
            refund = await RefundService.reject_refund(
                db=db,
                refund_id=refund_id,
                admin_id=current_user.user_id,
                admin_remark=request.admin_remark,
            )

        order = db.query(Order).filter(Order.order_id == refund.order_id).first()
        _broadcast_admin_refund_event(
            "refund_status_update",
            order,
            f"退款申请 {refund.refund_id} 已{ '批准' if request.action == 'approve' else '拒绝' }",
            {
                "refund_id": refund.refund_id,
                "status": refund.status,
                "admin_remark": refund.admin_remark,
            }
        )

        return APIResponse.success(
            RefundAuditResult(
                refund_id=refund.refund_id,
                status=refund.status,
                admin_remark=refund.admin_remark,
                approve_time=refund.approve_time,
            ),
            message="退款审核处理成功",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"退款审核失败: {str(e)}")


@router.get("/list", response_model=List[RefundResponse])
def get_refunds(
    status: Optional[str] = Query(None, description="退款状态：pending/approved/rejected/completed"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Refund).filter(Refund.user_id == current_user.user_id)
    if status:
        query = query.filter(Refund.status == status)
    refunds = query.order_by(Refund.create_time.desc()).limit(limit).offset(offset).all()
    return [
        RefundResponse(
            refund_id=r.refund_id,
            order_id=r.order_id,
            user_id=r.user_id,
            refund_amount=r.refund_amount,
            reason=r.reason,
            reason_category=r.reason_category,
            refund_items=r.refund_items,
            status=r.status,
            admin_remark=r.admin_remark,
            approve_time=r.approve_time.isoformat() if r.approve_time else None,
            auto_approved=r.auto_approved,
            create_time=r.create_time.isoformat(),
        )
        for r in refunds
    ]


@router.get("/statistics")
def get_refund_statistics(days: int = Query(30, ge=1, le=365, description="统计天数"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ("admin", "sys_admin", "merchant", "canteen_admin"):
        raise HTTPException(status_code=403, detail="需要管理员或商家权限")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    stats = RefundService.get_refund_statistics(db=db, start_date=start_date, end_date=end_date)

    if current_user.role in ("merchant", "canteen_admin"):
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current_user.user_id).first()
        if merchant_canteen:
            merchant_refunds = db.query(Refund).join(Order, Refund.order_id == Order.order_id).filter(
                Order.canteen_id == merchant_canteen.canteen_id,
                Refund.create_time >= start_date,
                Refund.create_time <= end_date,
            ).all()
            stats = {
                "total_count": len(merchant_refunds),
                "total_amount": float(sum(float(r.refund_amount or 0) for r in merchant_refunds)),
                "by_status": {
                    "pending": {"count": 0, "amount": 0.0},
                    "approved": {"count": 0, "amount": 0.0},
                    "rejected": {"count": 0, "amount": 0.0},
                    "completed": {"count": 0, "amount": 0.0},
                },
                "by_category": {},
                "auto_approved_count": sum(1 for r in merchant_refunds if r.auto_approved),
            }
            for refund in merchant_refunds:
                amount = float(refund.refund_amount or 0)
                status = refund.status or "pending"
                if status not in stats["by_status"]:
                    stats["by_status"][status] = {"count": 0, "amount": 0.0}
                stats["by_status"][status]["count"] += 1
                stats["by_status"][status]["amount"] += amount

                category = refund.reason_category or "other"
                if category not in stats["by_category"]:
                    stats["by_category"][category] = {"count": 0, "amount": 0.0}
                stats["by_category"][category]["count"] += 1
                stats["by_category"][category]["amount"] += amount

    return APIResponse.success(
        {
        "period": f"最近{days}天",
            "startTime": start_date.isoformat(),
            "endTime": end_date.isoformat(),
            "summary": stats,
    }
    )


@router.get("/{refund_id}", response_model=RefundResponse)
def get_refund_detail(refund_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    refund = db.query(Refund).filter(Refund.refund_id == refund_id).first()
    if not refund:
        raise HTTPException(status_code=404, detail="退款记录不存在")

    is_admin_or_merchant = current_user.role in ("admin", "sys_admin", "merchant", "canteen_admin")
    if refund.user_id != current_user.user_id:
        if not is_admin_or_merchant:
            raise HTTPException(status_code=403, detail="无权查看此退款记录")
        if current_user.role in ("merchant", "canteen_admin"):
            _check_merchant_refund_permission(current_user, refund_id, db)

    return RefundResponse(
        refund_id=refund.refund_id,
        order_id=refund.order_id,
        user_id=refund.user_id,
        refund_amount=refund.refund_amount,
        reason=refund.reason,
        reason_category=refund.reason_category,
        refund_items=refund.refund_items,
        status=refund.status,
        admin_remark=refund.admin_remark,
        approve_time=refund.approve_time.isoformat() if refund.approve_time else None,
        auto_approved=refund.auto_approved,
        create_time=refund.create_time.isoformat(),
    )
