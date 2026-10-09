from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import canteen_review as review_crud
from app.crud import order as order_crud
from app.schemas.canteen_review import CanteenReviewCreate, CanteenReviewOut

router = APIRouter(prefix="/review/canteen", tags=["canteen_review"])


@router.post("/create", response_model=CanteenReviewOut)
def create_canteen_review(
    payload: CanteenReviewCreate,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """创建档口评价"""
    # 验证订单是否属于当前用户
    order = order_crud.order.get(db, payload.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current.user_id:
        raise HTTPException(status_code=403, detail="无权评价此订单")
    if order.canteen_id != payload.canteen_id:
        raise HTTPException(status_code=400, detail="订单档口ID不匹配")
    
    # 检查是否已经评价过
    from app.models.canteen_review import CanteenReview
    existing = db.query(CanteenReview).filter(
        CanteenReview.order_id == payload.order_id,
        CanteenReview.user_id == current.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该订单已评价")
    
    # 创建评价
    from app.utils.pydantic import get_model_data
    review_data = get_model_data(payload)
    review_data["user_id"] = current.user_id
    db_obj = review_crud.canteen_review.create_by_dict(db, review_data)
    return db_obj


@router.get("/list/{canteen_id}", response_model=list[CanteenReviewOut])
def list_canteen_reviews(canteen_id: int, db: Session = Depends(deps.get_db)):
    """获取档口评价列表"""
    return review_crud.canteen_review.list_by_canteen(db, canteen_id)

