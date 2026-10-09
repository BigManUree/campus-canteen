from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.api import deps
from app.api.decorators import handle_api_errors
from app.crud import faq as faq_crud
from app.schemas.faq import FAQCreate, FAQUpdate, FAQOut
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/faq", tags=["faq"])


@router.get("/list", response_model=PaginatedResponse[FAQOut])
@handle_api_errors("获取FAQ列表失败")
def list_faqs(
    category: Optional[str] = Query(None, description="分类筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(deps.get_db)
):
    """获取常见问题列表（支持分页）"""
    from app.models.faq import FAQ
    
    query = db.query(FAQ).filter(FAQ.status == 1)
    
    if category:
        query = query.filter(FAQ.category == category)
    
    total = query.count()
    offset = (page - 1) * page_size
    # 处理sort_order可能为NULL的情况
    items = query.order_by(
        func.coalesce(FAQ.sort_order, 0).asc(), 
        FAQ.faq_id.desc()
    ).offset(offset).limit(page_size).all()
    
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/detail/{faq_id}", response_model=FAQOut)
def get_faq_detail(
    faq_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取FAQ详情（增加查看次数）"""
    faq = faq_crud.faq.get(db, faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    # 增加查看次数
    faq_crud.faq.increment_view(db, faq_id)
    
    return faq


@router.post("/create", response_model=FAQOut)
def create_faq(
    payload: FAQCreate,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """创建问题（管理端）"""
    return faq_crud.faq.create(db, payload)


@router.put("/update/{faq_id}", response_model=FAQOut)
def update_faq(
    faq_id: int,
    payload: FAQUpdate,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """更新问题（管理端）"""
    faq = faq_crud.faq.get(db, faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    # 使用 CRUD 的 update 方法
    faq = faq_crud.faq.update(db, faq_id, payload)
    if not faq:
        raise HTTPException(status_code=404, detail="问题不存在")
    return faq


@router.delete("/delete/{faq_id}")
def delete_faq(
    faq_id: int,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """删除问题（管理端）"""
    # 使用 CRUD 的 delete 方法
    faq_crud.faq.delete(db, faq_id)
    return {"success": True, "message": "问题已删除"}

