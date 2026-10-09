from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.api import deps
from app.crud import window as window_crud
from app.models.canteen import Canteen
from app.schemas.window import WindowCreate, WindowOut, WindowUpdate
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/window", tags=["window"])


def _ensure_canteen_exists(db: Session, canteen_id: Optional[int]):
    if canteen_id is None:
        raise HTTPException(status_code=400, detail="canteen_id 必填")
    canteen = db.query(Canteen).filter(Canteen.canteen_id == canteen_id).first()
    if not canteen:
        raise HTTPException(status_code=404, detail="食堂不存在")
    return canteen


def _merchant_canteen_id(current, db: Session) -> Optional[int]:
    from app.api.deps import is_merchant_role

    if not current or not is_merchant_role(current.role):
        return None

    canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
    if not canteen:
        raise HTTPException(status_code=403, detail="您还没有绑定食堂，请联系管理员分配")
    return canteen.canteen_id


@router.get("/list", response_model=PaginatedResponse[WindowOut])
def list_windows(
    keyword: Optional[str] = Query(None, description="窗口名称关键词"),
    canteen_id: Optional[int] = Query(None, description="食堂ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    merchant_canteen_id = _merchant_canteen_id(current, db)
    target_canteen_id = merchant_canteen_id if merchant_canteen_id is not None else canteen_id

    query = window_crud.window.search_windows(db, canteen_id=target_canteen_id, keyword=keyword).options(joinedload(window_crud.window.model.canteen))
    total = query.count()
    items = query.order_by(window_crud.window.model.sort_order.asc(), window_crud.window.model.window_id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/all", response_model=List[WindowOut])
def list_all_windows(
    keyword: Optional[str] = Query(None, description="窗口名称关键词"),
    canteen_id: Optional[int] = Query(None, description="食堂ID"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    merchant_canteen_id = _merchant_canteen_id(current, db)
    target_canteen_id = merchant_canteen_id if merchant_canteen_id is not None else canteen_id

    return window_crud.window.search_windows(db, canteen_id=target_canteen_id, keyword=keyword).options(joinedload(window_crud.window.model.canteen)).order_by(
        window_crud.window.model.sort_order.asc(), window_crud.window.model.window_id.asc()
    ).all()


@router.get("/detail/{window_id}", response_model=WindowOut)
def window_detail(window_id: int, db: Session = Depends(deps.get_db)):
    item = db.query(window_crud.window.model).options(joinedload(window_crud.window.model.canteen)).filter(window_crud.window.model.window_id == window_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="窗口不存在")
    return item


@router.post("/create", response_model=WindowOut)
def create_window(
    payload: WindowCreate,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    merchant_canteen_id = _merchant_canteen_id(current, db)
    target_canteen_id = merchant_canteen_id or payload.canteen_id
    _ensure_canteen_exists(db, target_canteen_id)

    existing = window_crud.window.get_by_name(db, payload.window_name, target_canteen_id)
    if existing:
        raise HTTPException(status_code=400, detail="同一食堂下窗口名称已存在")

    payload.canteen_id = target_canteen_id
    payload.parent_id = 0
    return window_crud.window.create(db, payload)


@router.put("/update/{window_id}", response_model=WindowOut)
def update_window(
    window_id: int,
    payload: WindowUpdate,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    item = window_crud.window.get(db, window_id)
    if not item:
        raise HTTPException(status_code=404, detail="窗口不存在")

    merchant_canteen_id = _merchant_canteen_id(current, db)
    if merchant_canteen_id is not None and item.canteen_id != merchant_canteen_id:
        raise HTTPException(status_code=403, detail="只能修改自己食堂的窗口")

    target_canteen_id = merchant_canteen_id or payload.canteen_id or item.canteen_id
    _ensure_canteen_exists(db, target_canteen_id)

    target_name = payload.window_name if payload.window_name is not None else item.window_name
    existing = window_crud.window.get_by_name(db, target_name, target_canteen_id)
    if existing and existing.window_id != item.window_id:
        raise HTTPException(status_code=400, detail="同一食堂下窗口名称已存在")

    payload.canteen_id = target_canteen_id
    if payload.parent_id is None:
        payload.parent_id = 0
    updated = window_crud.window.update(db, window_id, payload)
    return db.query(window_crud.window.model).options(joinedload(window_crud.window.model.canteen)).filter(window_crud.window.model.window_id == updated.window_id).first()


@router.delete("/delete/{window_id}")
def delete_window(
    window_id: int,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    item = window_crud.window.get(db, window_id)
    if not item:
        raise HTTPException(status_code=404, detail="窗口不存在")

    merchant_canteen_id = _merchant_canteen_id(current, db)
    if merchant_canteen_id is not None and item.canteen_id != merchant_canteen_id:
        raise HTTPException(status_code=403, detail="只能删除自己食堂的窗口")

    children = window_crud.window.list_by_parent(db, window_id)
    if children:
        raise HTTPException(status_code=400, detail="该窗口下存在子级数据，无法删除")

    if window_crud.window.has_dishes(db, window_id):
        raise HTTPException(status_code=400, detail="该窗口下仍有关联菜品，无法删除")

    window_crud.window.delete(db, window_id)
    return {"success": True, "message": "窗口已删除"}
