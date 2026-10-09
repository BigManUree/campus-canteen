from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import or_

from app.api import deps
from app.crud import dish as dish_crud
from app.models.dish import Dish
from app.models.window import Window
from app.schemas.dish import DishOut, DishCreate, DishUpdate, DishStatusUpdate
from app.schemas.common import PaginatedResponse
from app.schemas.batch import (
    BatchUpdateStatusRequest,
    BatchDeleteRequest,
    BatchUpdatePriceRequest,
    BatchExportRequest
)

router = APIRouter(prefix="/dish", tags=["dish"])


def _ensure_window_belongs_to_canteen(db: Session, canteen_id: int, window_id: Optional[int]):
    if not window_id:
        return
    window = db.query(Window).filter(Window.window_id == window_id).first()
    if not window:
        raise HTTPException(status_code=404, detail="窗口不存在")
    if window.canteen_id != canteen_id:
        raise HTTPException(status_code=400, detail="窗口不属于当前食堂")


def _attach_window_name(items: list[Dish], db: Session):
    window_ids = [item.window_id for item in items if getattr(item, "window_id", None)]
    if not window_ids:
        return items
    mapping = {
        row.window_id: row.window_name
        for row in db.query(Window).filter(Window.window_id.in_(window_ids)).all()
    }
    for item in items:
        item.window_name = mapping.get(item.window_id)
    return items


@router.get("/list", response_model=PaginatedResponse[DishOut])
def list_dishes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    canteen_id: Optional[int] = Query(None, description="食堂ID"),
    window_id: Optional[int] = Query(None, description="窗口ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[int] = Query(None, description="菜品状态：0=下架，1=上架，不传则返回所有"),
    sort_by: Optional[str] = Query("create_time", description="排序字段：price, sales, sales_count, view_count, favorite_count, create_time"),
    order: Optional[str] = Query("desc", description="排序方向：asc, desc"),
    _t: Optional[int] = Query(None, description="时间戳（防止缓存）"),
    db: Session = Depends(deps.get_db)
):
    query = db.query(Dish).filter(Dish.status != -1)

    if status is not None:
        query = query.filter(Dish.status == status)
    if canteen_id:
        query = query.filter(Dish.canteen_id == canteen_id)
    if window_id:
        query = query.filter(Dish.window_id == window_id)
    if keyword:
        query = query.filter(or_(Dish.name.like(f"%{keyword}%"), Dish.description.like(f"%{keyword}%")))

    if sort_by in ["sales", "sales_count"]:
        order_by = Dish.sales.desc() if order == "desc" else Dish.sales.asc()
    elif sort_by == "price":
        order_by = Dish.price.desc() if order == "desc" else Dish.price.asc()
    elif sort_by == "view_count":
        order_by = Dish.view_count.desc() if order == "desc" else Dish.view_count.asc()
    elif sort_by == "favorite_count":
        order_by = Dish.favorite_count.desc() if order == "desc" else Dish.favorite_count.asc()
    elif sort_by == "create_time":
        order_by = Dish.create_time.desc() if order == "desc" else Dish.create_time.asc()
    else:
        order_by = Dish.create_time.desc()

    total = query.count()
    offset = (page - 1) * page_size
    dishes = query.order_by(order_by).offset(offset).limit(page_size).all()
    _attach_window_name(dishes, db)
    return PaginatedResponse.create(items=dishes, total=total, page=page, page_size=page_size)


@router.get("/detail/{dish_id}", response_model=DishOut)
def dish_detail(
    dish_id: int,
    current=Depends(deps.get_current_user_optional),
    db: Session = Depends(deps.get_db)
):
    d = dish_crud.dish.get(db, dish_id)
    if not d or d.status != 1:
        raise HTTPException(status_code=404, detail="菜品不存在")

    dish_crud.dish.increment_view_count(db, dish_id)
    d = dish_crud.dish.get(db, dish_id)
    if d and d.window_id:
        window = db.query(Window).filter(Window.window_id == d.window_id).first()
        d.window_name = window.window_name if window else None

    if current:
        try:
            from app.models.browse_history import BrowseHistory
            from sqlalchemy import func

            existing = db.query(BrowseHistory).filter(
                BrowseHistory.user_id == current.user_id,
                BrowseHistory.dish_id == dish_id
            ).first()

            if existing:
                existing.browse_time = func.now()
            else:
                history = BrowseHistory(user_id=current.user_id, dish_id=dish_id)
                db.add(history)

            db.commit()
        except Exception as e:
            from app.core.logging import logger
            logger.warning(f"记录浏览历史失败: {e}")
            db.rollback()

    return d


@router.post("/create", response_model=DishOut)
def create_dish(
    payload: DishCreate,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    from app.api.deps import is_merchant_role
    if is_merchant_role(current.role):
        from app.models.canteen import Canteen
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            raise HTTPException(status_code=403, detail="您还没有绑定食堂，无法创建菜品")
        if payload.canteen_id != merchant_canteen.canteen_id:
            raise HTTPException(status_code=403, detail="只能在自己的食堂下创建菜品")
    _ensure_window_belongs_to_canteen(db, payload.canteen_id, payload.window_id)
    dish = dish_crud.dish.create(db, payload)
    _attach_window_name([dish], db)
    return dish


@router.put("/update/{dish_id}", response_model=DishOut)
def update_dish(
    dish_id: int,
    payload: DishUpdate,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    from app.api.deps import is_merchant_role
    if is_merchant_role(current.role):
        existing = dish_crud.dish.get(db, dish_id)
        if not existing:
            raise HTTPException(status_code=404, detail="菜品不存在")
        from app.models.canteen import Canteen
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen or existing.canteen_id != merchant_canteen.canteen_id:
            raise HTTPException(status_code=403, detail="只能修改自己食堂的菜品")
    existing = dish_crud.dish.get(db, dish_id)
    if not existing:
        raise HTTPException(status_code=404, detail="菜品不存在")
    target_canteen_id = payload.canteen_id if payload.canteen_id is not None else existing.canteen_id
    target_window_id = payload.window_id if payload.window_id is not None else existing.window_id
    _ensure_window_belongs_to_canteen(db, target_canteen_id, target_window_id)
    dish = dish_crud.dish.update(db, dish_id, payload)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    _attach_window_name([dish], db)
    return dish


@router.put("/status/{dish_id}", response_model=DishOut)
def update_dish_status(
    dish_id: int,
    payload: DishStatusUpdate,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    if payload.status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值必须为 0（下架）或 1（上架）")

    from app.api.deps import is_merchant_role
    if is_merchant_role(current.role):
        existing = dish_crud.dish.get(db, dish_id)
        if not existing:
            raise HTTPException(status_code=404, detail="菜品不存在")
        from app.models.canteen import Canteen
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen or existing.canteen_id != merchant_canteen.canteen_id:
            raise HTTPException(status_code=403, detail="只能修改自己食堂的菜品")

    dish = dish_crud.dish.update_status(db, dish_id, payload.status)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    _attach_window_name([dish], db)
    return dish


@router.get("/admin/list", response_model=list[DishOut])
def admin_list_dishes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    canteen_id: Optional[int] = Query(None, description="食堂ID筛选"),
    window_id: Optional[int] = Query(None, description="窗口ID筛选"),
    status: Optional[int] = Query(None, description="状态筛选（0下架，1上架）"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    from app.api.deps import is_merchant_role
    query = db.query(Dish).filter(Dish.status != -1)

    if is_merchant_role(current.role):
        from app.models.canteen import Canteen
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            return []
        canteen_id = merchant_canteen.canteen_id

    if canteen_id:
        query = query.filter(Dish.canteen_id == canteen_id)
    if window_id:
        query = query.filter(Dish.window_id == window_id)
    if status is not None:
        query = query.filter(Dish.status == status)
    if keyword:
        query = query.filter(or_(Dish.name.like(f"%{keyword}%"), Dish.description.like(f"%{keyword}%")))

    total = query.count()
    offset = (page - 1) * page_size
    dishes = query.order_by(Dish.dish_id.desc()).offset(offset).limit(page_size).all()
    _attach_window_name(dishes, db)
    return dishes


@router.delete("/delete/{dish_id}")
def delete_dish(
    dish_id: int,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    dish = db.query(Dish).filter(Dish.dish_id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")

    from app.api.deps import is_merchant_role
    if is_merchant_role(current.role):
        from app.models.canteen import Canteen
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen or dish.canteen_id != merchant_canteen.canteen_id:
            raise HTTPException(status_code=403, detail="只能删除自己食堂的菜品")

    dish.status = -1
    db.commit()
    return {"success": True, "message": "菜品已删除"}


@router.get("/stock/warning")
def get_stock_warning(
    threshold: int = Query(10, ge=0, description="库存预警阈值"),
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(100, ge=1, le=200, description="每页数量"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    from app.api.deps import is_merchant_role
    from app.models.canteen import Canteen

    query = db.query(Dish, Window.window_name).outerjoin(Window, Dish.window_id == Window.window_id).filter(Dish.status != -1)

    if is_merchant_role(current.role):
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            return {
                "records": [], "items": [], "total": 0, "pageNum": pageNum, "pageSize": pageSize,
                "totalPages": 0, "warning_count": 0, "zero_stock": [], "low_stock": []
            }
        query = query.filter(Dish.canteen_id == merchant_canteen.canteen_id)

    warning_rows = query.filter(Dish.stock <= threshold).order_by(Dish.stock.asc(), Dish.dish_id.desc()).all()
    total_dishes = query.count()

    rows, zero_stock, low_stock = [], [], []
    for dish, window_name in warning_rows:
        dish_info = {
            "dish_id": dish.dish_id,
            "dish_name": dish.name,
            "name": dish.name,
            "canteen_id": dish.canteen_id,
            "window_id": dish.window_id,
            "window_name": window_name or "未分配窗口",
            "stock": dish.stock,
            "current_stock": dish.stock,
            "warning_stock": threshold,
            "price": float(dish.price)
        }
        rows.append(dish_info)
        if dish.stock == 0:
            zero_stock.append(dish_info)
        else:
            low_stock.append(dish_info)

    total = len(rows)
    start = (pageNum - 1) * pageSize
    end = start + pageSize
    paged_rows = rows[start:end]
    total_pages = (total + pageSize - 1) // pageSize if pageSize > 0 else 0

    return {
        "records": paged_rows,
        "items": paged_rows,
        "list": paged_rows,
        "rows": paged_rows,
        "total": total,
        "pageNum": pageNum,
        "pageSize": pageSize,
        "totalPages": total_pages,
        "total_dishes": total_dishes,
        "warning_count": total,
        "zero_stock": zero_stock,
        "low_stock": low_stock
    }


@router.post("/batch/status")
def batch_update_dish_status(
    payload: BatchUpdateStatusRequest,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    if payload.status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值必须为 0（下架）或 1（上架）")

    from app.api.deps import is_merchant_role
    query = db.query(Dish).filter(Dish.dish_id.in_(payload.dish_ids), Dish.status != -1)
    if is_merchant_role(current.role):
        from app.models.canteen import Canteen
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            raise HTTPException(status_code=403, detail="您还没有绑定食堂")
        query = query.filter(Dish.canteen_id == merchant_canteen.canteen_id)

    dishes = query.all()
    if not dishes:
        raise HTTPException(status_code=404, detail="未找到可操作的菜品")

    updated_count = query.update({Dish.status: payload.status}, synchronize_session=False)
    db.commit()
    return {"success": True, "message": f"成功更新 {updated_count} 个菜品状态", "updated_count": updated_count}


@router.post("/batch/delete")
def batch_delete_dishes(
    payload: BatchDeleteRequest,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    from app.api.deps import is_merchant_role
    query = db.query(Dish).filter(Dish.dish_id.in_(payload.dish_ids), Dish.status != -1)
    if is_merchant_role(current.role):
        from app.models.canteen import Canteen
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            raise HTTPException(status_code=403, detail="您还没有绑定食堂")
        query = query.filter(Dish.canteen_id == merchant_canteen.canteen_id)

    dishes = query.all()
    if not dishes:
        raise HTTPException(status_code=404, detail="未找到可删除的菜品")

    deleted_count = query.update({Dish.status: -1}, synchronize_session=False)
    db.commit()
    return {"success": True, "message": f"成功删除 {deleted_count} 个菜品", "deleted_count": deleted_count}


@router.post("/batch/price")
def batch_update_dish_price(
    payload: BatchUpdatePriceRequest,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    from app.api.deps import is_merchant_role
    if payload.price <= 0:
        raise HTTPException(status_code=400, detail="价格必须大于 0")

    query = db.query(Dish).filter(Dish.dish_id.in_(payload.dish_ids), Dish.status != -1)
    if is_merchant_role(current.role):
        from app.models.canteen import Canteen
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            raise HTTPException(status_code=403, detail="您还没有绑定食堂")
        query = query.filter(Dish.canteen_id == merchant_canteen.canteen_id)

    dishes = query.all()
    if not dishes:
        raise HTTPException(status_code=404, detail="未找到可操作的菜品")

    updated_count = query.update({Dish.price: payload.price}, synchronize_session=False)
    db.commit()
    return {"success": True, "message": f"成功更新 {updated_count} 个菜品价格", "updated_count": updated_count}
