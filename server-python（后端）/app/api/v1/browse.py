"""浏览历史接口"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from app.api import deps
from app.api.decorators import handle_api_errors
from app.models.browse_history import BrowseHistory
from app.schemas.common import PaginatedResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/browse", tags=["browse"])


class DishInBrowse(BaseModel):
    """浏览历史中的菜品信息"""
    dish_id: int
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    images: Optional[str] = None
    stock: int
    sales: int = 0
    status: int
    canteen_id: int
    
    class Config:
        from_attributes = True


class BrowseHistoryOut(BaseModel):
    """浏览历史输出"""
    history_id: int
    dish_id: int
    user_id: int
    browse_time: datetime
    dish: Optional[DishInBrowse] = None
    
    class Config:
        from_attributes = True


@router.get("/history", response_model=PaginatedResponse[BrowseHistoryOut])
@handle_api_errors("获取浏览历史失败")
def get_browse_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """获取浏览历史列表
    
    返回用户浏览过的菜品，按浏览时间倒序排列
    """
    # 查询浏览历史，预加载菜品信息
    query = db.query(BrowseHistory).filter(
        BrowseHistory.user_id == current.user_id
    ).options(
        joinedload(BrowseHistory.dish)
    )
    
    total = query.count()
    offset = (page - 1) * page_size
    
    # 按浏览时间倒序（最近浏览的在前面）
    history = query.order_by(desc(BrowseHistory.browse_time)).offset(offset).limit(page_size).all()
    
    return PaginatedResponse.create(items=history, total=total, page=page, page_size=page_size)


@router.post("/add/{dish_id}")
@handle_api_errors("添加浏览历史失败")
def add_browse_history(
    dish_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """添加浏览历史
    
    如果该菜品已存在浏览记录，则更新浏览时间
    """
    # 检查是否已存在
    existing = db.query(BrowseHistory).filter(
        BrowseHistory.user_id == current.user_id,
        BrowseHistory.dish_id == dish_id
    ).first()
    
    if existing:
        # 更新浏览时间
        existing.browse_time = func.now()
        db.commit()
    else:
        # 创建新记录
        history = BrowseHistory(
            user_id=current.user_id,
            dish_id=dish_id
        )
        db.add(history)
        db.commit()
    
    return {"success": True, "message": "浏览历史已记录"}


@router.delete("/clear")
@handle_api_errors("清空浏览历史失败")
def clear_browse_history(
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """清空浏览历史
    
    删除当前用户的所有浏览记录
    """
    deleted_count = db.query(BrowseHistory).filter(
        BrowseHistory.user_id == current.user_id
    ).delete()
    
    db.commit()
    
    return {
        "success": True, 
        "message": "浏览历史已清空",
        "deleted_count": deleted_count
    }


@router.delete("/remove/{dish_id}")
@handle_api_errors("删除浏览记录失败")
def remove_browse_history(
    dish_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """删除单条浏览记录"""
    deleted_count = db.query(BrowseHistory).filter(
        BrowseHistory.user_id == current.user_id,
        BrowseHistory.dish_id == dish_id
    ).delete()
    
    db.commit()
    
    return {
        "success": True,
        "message": "浏览记录已删除",
        "deleted_count": deleted_count
    }

