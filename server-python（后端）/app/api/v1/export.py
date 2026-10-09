"""
数据导出API
支持导出订单、销售、用户、菜品数据为Excel/CSV格式
"""
from datetime import datetime, timedelta
import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, cast, Date, func
from sqlalchemy.orm import Session

from app.api import deps
from app.models.canteen import Canteen
from app.models.dish import Dish
from app.models.order import Order, OrderItem
from app.models.user import User

router = APIRouter(prefix="/statistics/export", tags=["export"])


def _parse_date_range(start_date: Optional[str], end_date: Optional[str]):
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) if end_date else None
    return start, end


def _format_export_filename(filename_prefix: str, export_format: str):
    ext = "xlsx" if export_format.lower() == "excel" else "csv"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"campus_canteen_{filename_prefix}_{timestamp}.{ext}"


def _format_order_status(status: Optional[int]) -> str:
    mapping = {
        0: "待确认",
        1: "制作中",
        2: "待取餐",
        3: "配送中",
        4: "已完成",
        5: "已取消",
    }
    return mapping.get(status, str(status) if status is not None else "")


def _format_pay_status(status: Optional[int]) -> str:
    mapping = {
        0: "未支付",
        1: "已支付",
    }
    return mapping.get(status, str(status) if status is not None else "")


def _format_order_type(order_type: Optional[str]) -> str:
    mapping = {
        "pickup": "到店自取",
        "delivery": "配送到点",
    }
    return mapping.get(order_type, order_type or "")


def _format_user_role(role: Optional[str]) -> str:
    mapping = {
        "admin": "管理员",
        "merchant": "商家",
        "user": "普通用户",
    }
    return mapping.get(role, role or "")


def _build_file_response(headers, rows, filename_prefix: str, sheet_name: str, export_format: str):
    if export_format.lower() == "excel":
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font

            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name
            ws.append(headers)

            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")

            for row in rows:
                ws.append(row)

            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            filename = _format_export_filename(filename_prefix, export_format)
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except ImportError:
            raise HTTPException(status_code=500, detail="需要安装openpyxl库：pip install openpyxl")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)

    filename = _format_export_filename(filename_prefix, export_format)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _build_order_export_query(
    db: Session,
    start_date: Optional[str],
    end_date: Optional[str],
    order_status: Optional[int],
    pay_status: Optional[int],
    canteen_id: Optional[int],
    current,
):
    query = db.query(Order, Canteen.canteen_name).join(
        Canteen, Order.canteen_id == Canteen.canteen_id
    )

    start, end = _parse_date_range(start_date, end_date)
    filters = []

    if start:
        filters.append(Order.create_time >= start)
    if end:
        filters.append(Order.create_time < end)
    if order_status is not None:
        filters.append(Order.order_status == order_status)
    if pay_status is not None:
        filters.append(Order.pay_status == pay_status)
    if canteen_id is not None:
        filters.append(Order.canteen_id == canteen_id)

    if deps.is_merchant_role(current.role):
        canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not canteen:
            raise HTTPException(status_code=404, detail="您还没有绑定档口，请联系管理员分配")
        filters.append(Order.canteen_id == canteen.canteen_id)

    if filters:
        query = query.filter(and_(*filters))

    return query.order_by(Order.order_id.desc()).all()


def _build_sales_export_query(
    db: Session,
    start_date: Optional[str],
    end_date: Optional[str],
    canteen_id: Optional[int],
    group_by: str,
    current,
):
    start, end = _parse_date_range(start_date, end_date)

    base_filters = [Order.order_status.in_([1, 2, 3, 4])]
    if start:
        base_filters.append(Order.create_time >= start)
    if end:
        base_filters.append(Order.create_time < end)

    if deps.is_merchant_role(current.role):
        canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not canteen:
            raise HTTPException(status_code=404, detail="您还没有绑定档口，请联系管理员分配")
        base_filters.append(Order.canteen_id == canteen.canteen_id)
    elif canteen_id is not None:
        base_filters.append(Order.canteen_id == canteen_id)

    if group_by == "canteen":
        query = db.query(
            Canteen.canteen_id.label("group_key"),
            Canteen.canteen_name.label("group_name"),
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.sum(OrderItem.price * OrderItem.quantity).label("total_amount"),
            func.count(func.distinct(Order.order_id)).label("order_count"),
        ).join(
            Order, Order.canteen_id == Canteen.canteen_id
        ).join(
            OrderItem, OrderItem.order_id == Order.order_id
        ).filter(
            and_(*base_filters)
        ).group_by(
            Canteen.canteen_id, Canteen.canteen_name
        ).order_by(
            func.sum(OrderItem.price * OrderItem.quantity).desc()
        )
        return query.all(), "canteen"

    if group_by in ["date", "day", "week", "month"]:
        order_date = cast(Order.create_time, Date)
        query = db.query(
            order_date.label("group_key"),
            func.sum(OrderItem.quantity).label("total_quantity"),
            func.sum(OrderItem.price * OrderItem.quantity).label("total_amount"),
            func.count(func.distinct(Order.order_id)).label("order_count"),
        ).join(
            OrderItem, OrderItem.order_id == Order.order_id
        ).filter(
            and_(*base_filters)
        ).group_by(
            order_date
        ).order_by(order_date)
        return query.all(), "date"

    query = db.query(
        Dish.dish_id,
        Dish.name,
        Canteen.canteen_name,
        func.sum(OrderItem.quantity).label("total_quantity"),
        func.sum(OrderItem.price * OrderItem.quantity).label("total_amount"),
        func.count(func.distinct(Order.order_id)).label("order_count"),
    ).join(
        OrderItem, Dish.dish_id == OrderItem.dish_id
    ).join(
        Order, OrderItem.order_id == Order.order_id
    ).join(
        Canteen, Dish.canteen_id == Canteen.canteen_id
    ).filter(
        and_(*base_filters)
    ).group_by(
        Dish.dish_id, Dish.name, Canteen.canteen_name
    ).order_by(
        func.sum(OrderItem.quantity).desc()
    )
    return query.all(), "dish"


@router.get("/orders")
def export_orders(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    order_status: Optional[int] = Query(None, description="订单状态"),
    pay_status: Optional[int] = Query(None, description="支付状态：0未支付，1已支付"),
    canteen_id: Optional[int] = Query(None, description="档口ID"),
    format: str = Query("csv", description="导出格式：csv 或 excel"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """导出订单数据（Excel/CSV）"""
    orders = _build_order_export_query(
        db=db,
        start_date=start_date,
        end_date=end_date,
        order_status=order_status,
        pay_status=pay_status,
        canteen_id=canteen_id,
        current=current,
    )

    headers = [
        "订单ID", "订单编号", "用户ID", "档口ID", "档口名称", "配送方式", "订单总额",
        "优惠金额", "实付金额", "支付状态", "订单状态", "取餐码", "下单时间"
    ]

    rows = [
        [
            order.order_id,
            order.order_no,
            order.user_id,
            order.canteen_id,
            canteen_name,
            _format_order_type(order.order_type),
            float(order.total_amount),
            float(order.discount_amount),
            float(order.pay_amount),
            _format_pay_status(order.pay_status),
            _format_order_status(order.order_status),
            order.pickup_code or "",
            order.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        ]
        for order, canteen_name in orders
    ]

    return _build_file_response(headers, rows, "orders", "订单数据", format)


@router.get("/sales")
def export_sales(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    canteen_id: Optional[int] = Query(None, description="档口ID"),
    group_by: str = Query("dish", description="分组方式：dish/canteen/date"),
    format: str = Query("csv", description="导出格式：csv 或 excel"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """导出销售数据（Excel/CSV）"""
    results, actual_group_by = _build_sales_export_query(
        db=db,
        start_date=start_date,
        end_date=end_date,
        canteen_id=canteen_id,
        group_by=group_by,
        current=current,
    )

    if actual_group_by == "canteen":
        headers = ["档口ID", "档口名称", "销售件数", "销售金额", "订单数"]
        rows = [
            [
                r.group_key,
                r.group_name,
                int(r.total_quantity or 0),
                float(r.total_amount or 0),
                int(r.order_count or 0),
            ]
            for r in results
        ]
        return _build_file_response(headers, rows, "sales", "按档口销售数据", format)

    if actual_group_by == "date":
        headers = ["日期", "销售件数", "销售金额", "订单数"]
        rows = [
            [
                r.group_key.strftime("%Y-%m-%d") if r.group_key else "",
                int(r.total_quantity or 0),
                float(r.total_amount or 0),
                int(r.order_count or 0),
            ]
            for r in results
        ]
        return _build_file_response(headers, rows, "sales", "按日期销售数据", format)

    headers = ["菜品ID", "菜品名称", "所属档口", "销售件数", "销售金额", "订单数"]
    rows = [
        [
            r.dish_id,
            r.name,
            r.canteen_name,
            int(r.total_quantity or 0),
            float(r.total_amount or 0),
            int(r.order_count or 0),
        ]
        for r in results
    ]
    return _build_file_response(headers, rows, "sales", "销售数据", format)


@router.get("/users")
def export_users(
    start_date: Optional[str] = Query(None, description="注册开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="注册结束日期 YYYY-MM-DD"),
    status: Optional[int] = Query(None, description="用户状态：0禁用，1正常"),
    format: str = Query("csv", description="导出格式：csv 或 excel"),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """导出用户数据（Excel/CSV）"""
    start, end = _parse_date_range(start_date, end_date)
    query = db.query(User)

    if start:
        query = query.filter(User.create_time >= start)
    if end:
        query = query.filter(User.create_time < end)
    if status is not None:
        query = query.filter(User.status == status)

    users = query.order_by(User.user_id.desc()).all()
    headers = ["用户ID", "用户名", "昵称", "手机号", "邮箱", "角色", "账号状态", "学院/部门", "学号/工号", "注册时间"]
    rows = [
        [
            user.user_id,
            user.username,
            user.nickname or "",
            user.phone or "",
            user.email or "",
            _format_user_role(user.role),
            "正常" if user.status == 1 else "禁用",
            user.department or "",
            user.student_no or "",
            user.create_time.strftime("%Y-%m-%d %H:%M:%S") if user.create_time else "",
        ]
        for user in users
    ]
    return _build_file_response(headers, rows, "users", "用户数据", format)


@router.get("/dishes")
def export_dishes(
    canteen_id: Optional[int] = Query(None, description="档口ID"),
    window_id: Optional[int] = Query(None, description="窗口ID"),
    status: Optional[int] = Query(None, description="菜品状态：0下架，1上架"),
    format: str = Query("csv", description="导出格式：csv 或 excel"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """导出菜品数据（Excel/CSV）"""
    query = db.query(Dish, Canteen.canteen_name).join(Canteen, Dish.canteen_id == Canteen.canteen_id)

    if deps.is_merchant_role(current.role):
        canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not canteen:
            raise HTTPException(status_code=404, detail="您还没有绑定档口，请联系管理员分配")
        query = query.filter(Dish.canteen_id == canteen.canteen_id)
    elif canteen_id is not None:
        query = query.filter(Dish.canteen_id == canteen_id)

    if window_id is not None:
        query = query.filter(Dish.window_id == window_id)
    if status is not None:
        query = query.filter(Dish.status == status)

    dishes = query.order_by(Dish.dish_id.desc()).all()
    headers = ["菜品ID", "菜品名称", "所属档口", "窗口ID", "单价", "库存", "累计销量", "浏览量", "收藏量", "上架状态", "创建时间"]
    rows = [
        [
            dish.dish_id,
            dish.name,
            canteen_name,
            dish.window_id,
            float(dish.price),
            int(dish.stock or 0),
            int(dish.sales or 0),
            int(dish.view_count or 0),
            int(dish.favorite_count or 0),
            "上架" if dish.status == 1 else "下架",
            dish.create_time.strftime("%Y-%m-%d %H:%M:%S") if dish.create_time else "",
        ]
        for dish, canteen_name in dishes
    ]
    return _build_file_response(headers, rows, "dishes", "菜品数据", format)
