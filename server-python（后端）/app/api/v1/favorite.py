from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Optional

from app.api import deps
from app.api.decorators import handle_api_errors
from app.crud import favorite as favorite_crud
from app.models.favorite import Favorite
from app.schemas.favorite import FavoriteOut, FavoriteToggle, FavoriteCreate
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/favorite", tags=["favorite"])


@router.post("/add")
@handle_api_errors("添加收藏失败")
def add_favorite(
    payload: FavoriteToggle,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    exist = favorite_crud.favorite.get_by_user_and_dish(db, current.user_id, payload.dish_id)
    if exist:
        return {"success": True}
    favorite_create = FavoriteCreate(user_id=current.user_id, dish_id=payload.dish_id)
    favorite_crud.favorite.create(db, favorite_create)
    return {"success": True}


@router.delete("/remove/{dish_id}")
@handle_api_errors("取消收藏失败")
def remove_favorite(
    dish_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """取消收藏（路径参数方式）
    
    Args:
        dish_id: 菜品ID（路径参数）
    
    Returns:
        操作结果
    """
    exist = favorite_crud.favorite.get_by_user_and_dish(db, current.user_id, dish_id)
    if exist:
        favorite_crud.favorite.delete(db, exist.favorite_id)
    return {"success": True}


@router.delete("/remove")
@handle_api_errors("取消收藏失败")
def remove_favorite_delete(
    dish_id: Optional[int] = Query(None, description="菜品ID（查询参数）"),
    payload: Optional[FavoriteToggle] = Body(None),
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """取消收藏（DELETE方式，支持查询参数或请求体）
    
    Args:
        dish_id: 菜品ID（查询参数，可选）
        payload: 包含 dish_id 的请求体（可选）
    
    Returns:
        操作结果
    """
    # 优先使用查询参数，其次使用请求体
    target_dish_id = dish_id
    if target_dish_id is None and payload is not None:
        target_dish_id = payload.dish_id
    
    if target_dish_id is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="缺少 dish_id 参数")
    
    exist = favorite_crud.favorite.get_by_user_and_dish(db, current.user_id, target_dish_id)
    if exist:
        favorite_crud.favorite.delete(db, exist.favorite_id)
    return {"success": True}


@router.post("/remove")
@handle_api_errors("取消收藏失败")
def remove_favorite_post(
    payload: FavoriteToggle,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """取消收藏（POST方式，兼容旧版前端）
    
    Args:
        payload: 包含 dish_id 的请求体
    
    Returns:
        操作结果
    """
    exist = favorite_crud.favorite.get_by_user_and_dish(db, current.user_id, payload.dish_id)
    if exist:
        favorite_crud.favorite.delete(db, exist.favorite_id)
    return {"success": True}


@router.get("/check/{dish_id}")
@handle_api_errors("检查收藏状态失败")
def check_favorite(
    dish_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """检查菜品是否已收藏"""
    exist = favorite_crud.favorite.get_by_user_and_dish(db, current.user_id, dish_id)
    return {
        "is_favorite": exist is not None,
        "favorite_id": exist.favorite_id if exist else None
    }


@router.get("/list", response_model=PaginatedResponse[FavoriteOut])
@handle_api_errors("获取收藏列表失败")
def list_favorites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    from sqlalchemy.orm import joinedload
    
    # 获取收藏列表，使用 joinedload 预加载菜品信息，避免 N+1 查询
    query = db.query(Favorite).filter(Favorite.user_id == current.user_id).options(
        joinedload(Favorite.dish)
    )
    
    total = query.count()
    offset = (page - 1) * page_size
    favorites = query.order_by(Favorite.create_time.desc()).offset(offset).limit(page_size).all()
    
    return PaginatedResponse.create(items=favorites, total=total, page=page, page_size=page_size)


