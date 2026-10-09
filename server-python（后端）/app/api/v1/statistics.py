"""
数据统计看板API
提供菜品销量、时间段热度、用户偏好等统计数据
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Date, and_, cast, func
from sqlalchemy.orm import Session

from app.api import deps
from app.models.canteen import Canteen
from app.models.dish import Dish
from app.models.order import Order, OrderItem
from app.models.refund import Refund
from app.models.user import User
from app.schemas.common import APIResponse

router = APIRouter(prefix="/statistics", tags=["statistics"])

VALID_ORDER_STATUSES = [0, 1, 2, 3, 4]
COMPLETED_ORDER_STATUSES = [2, 4]


def ok(data, message: str = "success"):
    return APIResponse.success(data=data, message=message)



def _get_merchant_dashboard_data(current, db: Session, debug: bool = False):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today + timedelta(days=1)

    order_query = db.query(Order)
    refund_query = db.query(Refund).join(Order, Refund.order_id == Order.order_id)
    canteen_query = db.query(Canteen)
    user_query = db.query(User)

    if deps.is_merchant_role(current.role):
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            raise HTTPException(status_code=404, detail="您还没有绑定食堂，请联系管理员分配")
        order_query = order_query.filter(Order.canteen_id == merchant_canteen.canteen_id)
        refund_query = refund_query.filter(Order.canteen_id == merchant_canteen.canteen_id)
        canteen_query = canteen_query.filter(Canteen.canteen_id == merchant_canteen.canteen_id)

    today_orders = order_query.filter(
        Order.create_time >= today,
        Order.create_time < today_end,
        Order.order_status.in_(VALID_ORDER_STATUSES),
    ).count()
    today_sales = order_query.filter(
        Order.pay_status == 1,
        Order.create_time >= today,
        Order.create_time < today_end,
        Order.order_status.in_(COMPLETED_ORDER_STATUSES),
    ).with_entities(func.sum(Order.pay_amount)).scalar() or 0
    pending_orders = order_query.filter(Order.pay_status == 1, Order.order_status == 1).count()
    ready_count = order_query.filter(Order.pay_status == 1, Order.order_status == 2).count()
    pending_refunds = refund_query.filter(Refund.status == "pending").count()
    active_canteens = canteen_query.filter(Canteen.status == 1).count()

    if deps.is_merchant_role(current.role):
        today_new_users = 0
    else:
        today_new_users = user_query.filter(User.create_time >= today, User.create_time < today_end).count()

    top_dish_rows = order_query.filter(
        Order.pay_status == 1,
        Order.create_time >= today,
        Order.create_time < today_end,
        Order.order_status.in_(COMPLETED_ORDER_STATUSES),
    ).join(
        OrderItem, OrderItem.order_id == Order.order_id
    ).join(
        Dish, Dish.dish_id == OrderItem.dish_id
    ).with_entities(
        Dish.dish_id.label("dish_id"),
        Dish.name.label("dish_name"),
        func.sum(OrderItem.quantity).label("total_sales"),
        func.sum(OrderItem.quantity * OrderItem.price).label("total_amount"),
        func.count(func.distinct(Order.order_id)).label("order_count"),
    ).group_by(
        Dish.dish_id,
        Dish.name,
    ).order_by(
        func.sum(OrderItem.quantity).desc(),
        Dish.dish_id.asc(),
    ).limit(10).all()

    matched_order_rows = []
    if debug:
        matched_order_rows = order_query.filter(
            Order.pay_status == 1,
            Order.create_time >= today,
            Order.create_time < today_end,
            Order.order_status.in_(COMPLETED_ORDER_STATUSES),
        ).join(
            OrderItem, OrderItem.order_id == Order.order_id
        ).with_entities(
            Order.order_id.label("order_id"),
            Order.order_no.label("order_no"),
            Order.pay_status.label("pay_status"),
            Order.order_status.label("order_status"),
            Order.create_time.label("create_time"),
            OrderItem.dish_id.label("dish_id"),
            OrderItem.dish_name.label("dish_name"),
            OrderItem.quantity.label("quantity"),
            OrderItem.price.label("price"),
        ).order_by(
            Order.create_time.desc(),
            Order.order_id.desc(),
            OrderItem.item_id.asc(),
        ).all()

    top_dishes = [
        {
            "dish_id": row.dish_id,
            "dish_name": row.dish_name,
            "total_sales": int(row.total_sales or 0),
            "sales_count": int(row.total_sales or 0),
            "order_count": int(row.order_count or 0),
            "total_amount": float(row.total_amount or 0),
        }
        for row in top_dish_rows
    ]

    response_data = {
        "today": {
            "order_count": int(today_orders),
            "amount": float(today_sales),
            "new_users": int(today_new_users),
        },
        "today_orders": int(today_orders),
        "today_amount": float(today_sales),
        "todayOrderCount": int(today_orders),
        "todaySalesAmount": float(today_sales),
        "todayNewUserCount": int(today_new_users),
        "pendingOrderCount": int(pending_orders),
        "pending_orders": int(pending_orders),
        "ready_count": int(ready_count),
        "readyCount": int(ready_count),
        "pendingRefundCount": int(pending_refunds),
        "pending_refunds": int(pending_refunds),
        "activeStallCount": int(active_canteens),
        "top_dishes": top_dishes,
    }

    if debug:
        response_data["debug"] = {
            "filters": {
                "today_start": today.isoformat(),
                "today_end": today_end.isoformat(),
                "pay_status": 1,
                "order_statuses": COMPLETED_ORDER_STATUSES,
            },
            "matched_order_count": len({row.order_id for row in matched_order_rows}),
            "matched_item_count": len(matched_order_rows),
            "matched_orders": [
                {
                    "order_id": row.order_id,
                    "order_no": row.order_no,
                    "pay_status": int(row.pay_status or 0),
                    "order_status": int(row.order_status or 0),
                    "create_time": row.create_time.isoformat() if row.create_time else None,
                    "dish_id": row.dish_id,
                    "dish_name": row.dish_name,
                    "quantity": int(row.quantity or 0),
                    "price": float(row.price or 0),
                }
                for row in matched_order_rows
            ],
            "aggregated_top_dishes": top_dishes,
        }

    return response_data


@router.get("/dashboard")
def dashboard_statistics(
    debug: bool = Query(False, description="是否返回调试信息"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db),
):
    """管理后台看板汇总接口"""
    return ok(_get_merchant_dashboard_data(current=current, db=db, debug=debug))


@router.get("/merchant/overview")
def merchant_overview_statistics(
    debug: bool = Query(False, description="是否返回调试信息"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db),
):
    """商家端概览统计接口（兼容旧前端路径）"""
    return ok(_get_merchant_dashboard_data(current=current, db=db, debug=debug))


@router.get("/sales/trend-admin")
def sales_trend_admin(
    mode: str = Query("day", pattern="^(day|week|month)$"),
    startTime: Optional[datetime] = Query(None),
    endTime: Optional[datetime] = Query(None),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    """后台销售趋势接口"""
    if endTime is None:
        endTime = datetime.now()
    if startTime is None:
        delta_days = 30 if mode == "day" else 84 if mode == "week" else 365
        startTime = endTime - timedelta(days=delta_days)

    rows = db.query(
        cast(Order.create_time, Date).label("date"),
        func.count(Order.order_id).label("order_count"),
        func.sum(Order.pay_amount).label("sales_amount"),
    ).filter(
        Order.pay_status == 1,
        Order.create_time >= startTime,
        Order.create_time <= endTime,
    ).group_by(cast(Order.create_time, Date)).order_by(cast(Order.create_time, Date)).all()

    return ok({
        "mode": mode,
        "startTime": startTime.isoformat(),
        "endTime": endTime.isoformat(),
        "records": [
            {
                "date": row.date.isoformat(),
                "orderCount": int(row.order_count or 0),
                "salesAmount": float(row.sales_amount or 0),
            }
            for row in rows
        ],
    })


@router.get("/ranking/dishes")
def dish_ranking(
    limit: int = Query(10, ge=1, le=50),
    startTime: Optional[datetime] = Query(None),
    endTime: Optional[datetime] = Query(None),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    query = db.query(
        Dish.dish_id,
        Dish.name,
        Dish.sales,
        func.sum(OrderItem.quantity).label("sales_count"),
        func.sum(OrderItem.quantity * OrderItem.price).label("sales_amount"),
    ).join(OrderItem, Dish.dish_id == OrderItem.dish_id).join(Order, OrderItem.order_id == Order.order_id).filter(Order.pay_status == 1)

    if startTime is not None:
        query = query.filter(Order.create_time >= startTime)
    if endTime is not None:
        query = query.filter(Order.create_time <= endTime)

    rows = query.group_by(Dish.dish_id, Dish.name, Dish.sales).order_by(func.sum(OrderItem.quantity).desc()).limit(limit).all()
    return ok([
        {
            "dishId": row.dish_id,
            "id": row.dish_id,
            "dishName": row.name,
            "name": row.name,
            "salesCount": int(row.sales_count or 0),
            "sales": int(row.sales_count or row.sales or 0),
            "salesAmount": float(row.sales_amount or 0),
            "amount": float(row.sales_amount or 0),
        }
        for row in rows
    ])


@router.get("/ranking/stalls")
def stall_ranking(
    limit: int = Query(10, ge=1, le=50),
    startTime: Optional[datetime] = Query(None),
    endTime: Optional[datetime] = Query(None),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    query = db.query(
        Canteen.canteen_id,
        Canteen.canteen_name,
        func.count(Order.order_id).label("order_count"),
        func.sum(Order.pay_amount).label("sales_amount"),
    ).join(Order, Canteen.canteen_id == Order.canteen_id).filter(Order.pay_status == 1)

    if startTime is not None:
        query = query.filter(Order.create_time >= startTime)
    if endTime is not None:
        query = query.filter(Order.create_time <= endTime)

    rows = query.group_by(Canteen.canteen_id, Canteen.canteen_name).order_by(func.sum(Order.pay_amount).desc()).limit(limit).all()
    return ok([
        {
            "stallId": row.canteen_id,
            "stallName": row.canteen_name,
            "orderCount": int(row.order_count or 0),
            "salesAmount": float(row.sales_amount or 0),
        }
        for row in rows
    ])


@router.get("/users/growth")
def user_growth(
    startTime: Optional[datetime] = Query(None),
    endTime: Optional[datetime] = Query(None),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    if endTime is None:
        endTime = datetime.now()
    if startTime is None:
        startTime = endTime - timedelta(days=30)

    rows = db.query(
        cast(User.create_time, Date).label("date"),
        func.count(User.user_id).label("new_user_count"),
    ).filter(
        User.create_time >= startTime,
        User.create_time <= endTime,
    ).group_by(cast(User.create_time, Date)).order_by(cast(User.create_time, Date)).all()

    return ok([
        {
            "date": row.date.isoformat(),
            "newUserCount": int(row.new_user_count or 0),
        }
        for row in rows
    ])


@router.get("/refund/summary")
def refund_summary(
    startTime: Optional[datetime] = Query(None),
    endTime: Optional[datetime] = Query(None),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    if endTime is None:
        endTime = datetime.now()
    if startTime is None:
        startTime = endTime - timedelta(days=30)

    refunds_query = db.query(Refund).filter(Refund.create_time >= startTime, Refund.create_time <= endTime)
    refund_count = refunds_query.count()
    refund_amount = refunds_query.with_entities(func.sum(Refund.refund_amount)).scalar() or 0
    paid_order_count = db.query(func.count(Order.order_id)).filter(
        Order.pay_status == 1,
        Order.create_time >= startTime,
        Order.create_time <= endTime,
    ).scalar() or 0
    refund_rate = (refund_count / paid_order_count) if paid_order_count else 0

    return ok({
        "refundCount": int(refund_count),
        "refundAmount": float(refund_amount),
        "refundRate": round(float(refund_rate), 4),
    })


@router.get("/overview")
def overview_statistics(
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    """数据看板概览统计"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today + timedelta(days=1)

    today_orders = db.query(func.count(Order.order_id)).filter(
        and_(
            Order.create_time >= today,
            Order.create_time < today_end,
        )
    ).scalar() or 0

    today_amount = db.query(func.sum(Order.pay_amount)).filter(
        and_(
            Order.create_time >= today,
            Order.create_time < today_end,
            Order.pay_status == 1,
        )
    ).scalar() or 0

    today_new_users = db.query(func.count(User.user_id)).filter(
        and_(
            User.create_time >= today,
            User.create_time < today_end,
        )
    ).scalar() or 0

    total_orders = db.query(func.count(Order.order_id)).filter(
        Order.order_status.in_([1, 2, 3, 4])
    ).scalar() or 0

    total_amount = db.query(func.sum(Order.pay_amount)).filter(
        Order.pay_status == 1
    ).scalar() or 0

    total_dishes = db.query(func.count(Dish.dish_id)).filter(Dish.status == 1).scalar() or 0
    total_users = db.query(func.count(User.user_id)).filter(User.status == 1).scalar() or 0
    pending_confirm_orders = db.query(func.count(Order.order_id)).filter(Order.order_status == 0).scalar() or 0
    pending_refunds = db.query(func.count(Refund.refund_id)).filter(Refund.status == "pending").scalar() or 0
    total_pending = pending_confirm_orders + pending_refunds

    return ok({
        "today": {
            "order_count": int(today_orders),
            "amount": float(today_amount),
            "new_users": int(today_new_users),
        },
        "total": {
            "order_count": int(total_orders),
            "amount": float(total_amount),
        },
        "dishes": {
            "total": int(total_dishes),
        },
        "users": {
            "total": int(total_users),
            "today_new": int(today_new_users),
        },
        "pending": {
            "order_count": int(total_pending),
            "pending_confirm": int(pending_confirm_orders),
            "pending_refunds": int(pending_refunds),
        },
    })


@router.get("/dish/sales")
def dish_sales_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(10, description="返回数量"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db),
):
    """菜品销量统计"""
    query = db.query(
        Dish.dish_id,
        Dish.name,
        func.sum(OrderItem.quantity).label("total_quantity"),
        func.sum(OrderItem.price * OrderItem.quantity).label("total_amount"),
        func.count(OrderItem.item_id).label("order_count"),
    ).join(
        OrderItem, Dish.dish_id == OrderItem.dish_id
    ).join(
        Order, OrderItem.order_id == Order.order_id
    ).filter(
        Order.order_status.in_([1, 2, 3, 4])
    )

    if deps.is_merchant_role(current.role):
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            raise HTTPException(status_code=404, detail="您还没有绑定档口，请联系管理员分配")
        query = query.filter(Order.canteen_id == merchant_canteen.canteen_id)

    if start_date:
        query = query.filter(Order.create_time >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Order.create_time < end)

    results = query.group_by(Dish.dish_id, Dish.name).order_by(func.sum(OrderItem.quantity).desc()).limit(limit).all()

    return ok([
        {
            "dish_id": r.dish_id,
            "dish_name": r.name,
            "total_quantity": int(r.total_quantity or 0),
            "total_amount": float(r.total_amount or 0),
            "order_count": int(r.order_count or 0),
        }
        for r in results
    ])


@router.get("/time/heat")
def time_heat_statistics(
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD，默认今天"),
    canteen_id: Optional[int] = Query(None, description="档口ID，可选"),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    """时间段热度统计（按小时）"""
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        target_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    start_time = target_date
    end_time = target_date + timedelta(days=1)

    query = db.query(
        func.extract("hour", Order.create_time).label("hour"),
        func.count(Order.order_id).label("order_count"),
        func.sum(Order.pay_amount).label("total_amount"),
    ).filter(
        and_(
            Order.create_time >= start_time,
            Order.create_time < end_time,
            Order.order_status.in_([1, 2, 3, 4]),
        )
    )

    if canteen_id is not None:
        query = query.filter(Order.canteen_id == canteen_id)

    results = query.group_by(
        func.extract("hour", Order.create_time)
    ).order_by(
        func.extract("hour", Order.create_time)
    ).all()

    hour_data = {r.hour: {"order_count": int(r.order_count), "total_amount": float(r.total_amount or 0)} for r in results}
    full_data = []
    for hour in range(24):
        data = hour_data.get(hour, {"order_count": 0, "total_amount": 0})
        full_data.append({
            "hour": hour,
            "order_count": data["order_count"],
            "total_amount": data["total_amount"],
        })

    return ok({
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "canteen_id": canteen_id,
        "hourly_data": full_data,
    })


@router.get("/user/preference")
def user_preference_statistics(
    limit: int = Query(10, description="返回数量"),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    """用户偏好统计（最受欢迎的菜品）"""
    results = db.query(
        Dish.dish_id,
        Dish.name,
        Dish.view_count,
        Dish.favorite_count,
        func.sum(OrderItem.quantity).label("sales_count"),
    ).outerjoin(
        OrderItem, Dish.dish_id == OrderItem.dish_id
    ).outerjoin(
        Order, and_(
            OrderItem.order_id == Order.order_id,
            Order.order_status.in_([1, 2, 3, 4]),
        )
    ).filter(
        Dish.status == 1
    ).group_by(
        Dish.dish_id, Dish.name, Dish.view_count, Dish.favorite_count
    ).order_by(
        (Dish.view_count + Dish.favorite_count * 2 + func.coalesce(func.sum(OrderItem.quantity), 0)).desc()
    ).limit(limit).all()

    return ok([
        {
            "dish_id": r.dish_id,
            "dish_name": r.name,
            "view_count": int(r.view_count or 0),
            "favorite_count": int(r.favorite_count or 0),
            "sales_count": int(r.sales_count or 0),
            "popularity_score": int((r.view_count or 0) + (r.favorite_count or 0) * 2 + (r.sales_count or 0)),
        }
        for r in results
    ])


@router.get("/sales/trend")
def sales_trend_statistics(
    days: int = Query(7, ge=1, le=90, description="统计天数，默认7天"),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    """销售趋势统计（按日期）"""
    end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    start_date = (end_date - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    results = db.query(
        cast(Order.create_time, Date).label("date"),
        func.count(Order.order_id).label("order_count"),
        func.sum(Order.pay_amount).label("total_amount"),
    ).filter(
        and_(
            Order.create_time >= start_date,
            Order.create_time <= end_date,
            Order.pay_status == 1,
        )
    ).group_by(
        cast(Order.create_time, Date)
    ).order_by(
        cast(Order.create_time, Date)
    ).all()

    date_data = {r.date.strftime("%Y-%m-%d"): {"order_count": int(r.order_count), "total_amount": float(r.total_amount or 0)} for r in results}

    trend_data = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        data = date_data.get(date_str, {"order_count": 0, "total_amount": 0})
        trend_data.append({
            "date": date_str,
            "order_count": data["order_count"],
            "total_amount": data["total_amount"],
        })
        current_date += timedelta(days=1)

    return ok({
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "days": days,
        "trend_data": trend_data,
    })


@router.get("/dish/popular")
def popular_dishes_statistics(
    limit: int = Query(10, ge=1, le=50, description="返回数量，默认10"),
    days: int = Query(30, ge=1, le=365, description="统计天数，默认30天"),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    """热门菜品统计"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    sales_subquery = db.query(
        OrderItem.dish_id,
        func.sum(OrderItem.quantity).label("sales_count"),
    ).join(
        Order, OrderItem.order_id == Order.order_id
    ).filter(
        and_(
            Order.create_time >= start_date,
            Order.create_time <= end_date,
            Order.pay_status == 1,
        )
    ).group_by(OrderItem.dish_id).subquery()

    results = db.query(
        Dish.dish_id,
        Dish.name,
        Dish.view_count,
        Dish.favorite_count,
        func.coalesce(sales_subquery.c.sales_count, 0).label("sales_count"),
    ).outerjoin(
        sales_subquery, Dish.dish_id == sales_subquery.c.dish_id
    ).filter(
        Dish.status == 1
    ).order_by(
        (func.coalesce(sales_subquery.c.sales_count, 0) + Dish.favorite_count * 2 + Dish.view_count).desc()
    ).limit(limit).all()

    return ok([
        {
            "dish_id": r.dish_id,
            "dish_name": r.name,
            "view_count": int(r.view_count or 0),
            "favorite_count": int(r.favorite_count or 0),
            "sales_count": int(r.sales_count or 0),
        }
        for r in results
    ])
