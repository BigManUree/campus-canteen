from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.api import deps
from app.api.decorators import handle_api_errors
from app.crud import review as review_crud
from app.schemas.review import ReviewCreate, ReviewOut, ReviewReplyIn
from app.schemas.common import PaginatedResponse
from app.models.review import Review
from app.models.order import Order, OrderItem

router = APIRouter(prefix="/review", tags=["review"])


@router.post("/create", response_model=ReviewOut)
@handle_api_errors("创建评价失败")
async def create_review(
    request: Request,
    payload: ReviewCreate,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """创建评价，支持图片和音视频"""
    from app.core.logging import logger
    
    # 记录请求数据用于调试
    try:
        body = await request.body()
        logger.info(f"评价创建请求 - 原始数据: {body.decode('utf-8')}")
        logger.info(
            "评价创建请求 - 解析后: "
            f"order_id={payload.order_id}, dish_id={payload.dish_id}, rating={payload.rating}, "
            f"is_anonymous={payload.is_anonymous}"
        )
    except Exception as e:
        logger.warning(f"无法记录请求数据: {e}")
    
    # 验证订单是否存在且属于当前用户
    order = db.query(Order).filter(Order.order_id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current.user_id:
        raise HTTPException(status_code=403, detail="无权评价此订单")
    
    # 验证订单中是否包含该菜品
    order_item = db.query(OrderItem).filter(
        OrderItem.order_id == payload.order_id,
        OrderItem.dish_id == payload.dish_id
    ).first()
    if not order_item:
        raise HTTPException(status_code=400, detail="该订单中不包含此菜品")
    
    # 检查是否已评价
    existing = db.query(Review).filter(
        Review.order_id == payload.order_id,
        Review.dish_id == payload.dish_id,
        Review.user_id == current.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该菜品已评价")
    
    # 创建评价
    review_data = {
        "order_id": payload.order_id,
        "dish_id": payload.dish_id,
        "user_id": current.user_id,
        "rating": payload.rating,
        "content": payload.content,
        "images": payload.images,
        "media_path": payload.media_path,
        "media_type": payload.media_type,
        "is_anonymous": payload.is_anonymous,
    }
    db_obj = review_crud.review.create_by_dict(db, review_data)
    return db_obj


@router.get("/list/{dish_id}", response_model=PaginatedResponse[ReviewOut])
@handle_api_errors("获取评价列表失败")
def list_reviews(
    dish_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="评分筛选（1-5）"),
    db: Session = Depends(deps.get_db)
):
    from sqlalchemy.orm import joinedload

    query = db.query(Review).filter(Review.dish_id == dish_id).options(
        joinedload(Review.user)
    )

    if rating is not None:
        query = query.filter(Review.rating == rating)

    total = query.count()
    offset = (page - 1) * page_size
    reviews = (
        query.order_by(Review.create_time.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse.create(
        items=reviews, total=total, page=page, page_size=page_size
    )


@router.get("/order/{order_id}")
def get_order_review_info(
    order_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """根据订单获取可评价的菜品列表"""
    from app.models.dish import Dish
    from app.utils.image import get_first_image_url
    
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current.user_id and current.role not in ["admin", "sys_admin", "merchant", "canteen_admin"]:
        raise HTTPException(status_code=403, detail="无权查看此订单的评价信息")

    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

    if not items:
        return {
            "order_id": order.order_id,
            "canteen_id": order.canteen_id,
            "items": [],
        }

    existing_reviews = (
        db.query(Review)
        .filter(Review.order_id == order_id, Review.user_id == current.user_id)
        .all()
    )
    reviewed_map = {(r.dish_id): r for r in existing_reviews}

    result_items = []
    for item in items:
        r = reviewed_map.get(item.dish_id)
        dish = db.query(Dish).filter(Dish.dish_id == item.dish_id).first()
        image_url = get_first_image_url(dish.images) if dish else None
        result_items.append(
            {
                "dish_id": item.dish_id,
                "dish_name": item.dish_name,
                "price": float(item.price),
                "quantity": item.quantity,
                "image": image_url,
                "reviewed": bool(r),
                "review_id": r.review_id if r else None,
            }
        )

    return {
        "order_id": order.order_id,
        "canteen_id": order.canteen_id,
        "items": result_items,
    }


@router.get("/admin/list")
@handle_api_errors("获取评价管理列表失败")
def admin_list_reviews(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    dish_id: Optional[int] = Query(None, description="菜品ID筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="评分筛选（1-5）"),
    keyword: Optional[str] = Query(None, description="关键词搜索（评价内容）"),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """管理端获取所有评价列表"""
    from sqlalchemy.orm import joinedload

    query = db.query(Review).options(
        joinedload(Review.user),
        joinedload(Review.dish)
    )
    
    if dish_id is not None:
        query = query.filter(Review.dish_id == dish_id)
    if user_id is not None:
        query = query.filter(Review.user_id == user_id)
    if rating is not None:
        query = query.filter(Review.rating == rating)
    if keyword:
        query = query.filter(Review.content.like(f"%{keyword}%"))
    
    total = query.count()
    offset = (page - 1) * page_size
    reviews = (
        query.order_by(Review.create_time.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    
    items = []
    for review in reviews:
        items.append({
            "review_id": review.review_id,
            "order_id": review.order_id,
            "dish_id": review.dish_id,
            "dish_name": review.dish.name if review.dish else None,
            "user_id": review.user_id,
            "username": review.user.username if review.user else None,
            "rating": review.rating,
            "content": review.content,
            "images": review.images,
            "media_path": review.media_path,
            "media_type": review.media_type,
            "reply_content": review.reply_content,
            "reply_time": review.reply_time.strftime("%Y-%m-%d %H:%M:%S") if review.reply_time else None,
            "reply_user_id": review.reply_user_id,
            "create_time": review.create_time.strftime("%Y-%m-%d %H:%M:%S") if review.create_time else None
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/merchant/list")
@handle_api_errors("获取商家评价列表失败")
def merchant_list_reviews(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="评分筛选（1-5）"),
    keyword: Optional[str] = Query(None, description="关键词搜索（评价内容）"),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """商家获取自己档口评价列表"""
    from sqlalchemy.orm import joinedload
    from app.models.dish import Dish
    from app.models.canteen import Canteen

    query = db.query(Review).options(
        joinedload(Review.user),
        joinedload(Review.dish)
    )

    if current.role == "merchant":
        merchant_canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
        if not merchant_canteen:
            raise HTTPException(status_code=404, detail="您还没有绑定档口，请联系管理员分配")
        query = query.join(Dish, Review.dish_id == Dish.dish_id).filter(Dish.canteen_id == merchant_canteen.canteen_id)

    if rating is not None:
        query = query.filter(Review.rating == rating)
    if keyword:
        query = query.filter(Review.content.like(f"%{keyword}%"))

    total = query.count()
    offset = (page - 1) * page_size
    reviews = (
        query.order_by(Review.create_time.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = []
    for review in reviews:
        items.append({
            "review_id": review.review_id,
            "order_id": review.order_id,
            "dish_id": review.dish_id,
            "dish_name": review.dish.name if review.dish else None,
            "canteen_id": review.dish.canteen_id if review.dish else None,
            "user_id": review.user_id,
            "username": review.user.username if review.user else None,
            "rating": review.rating,
            "content": review.content,
            "images": review.images,
            "media_path": review.media_path,
            "media_type": review.media_type,
            "reply_content": review.reply_content,
            "reply_time": review.reply_time.strftime("%Y-%m-%d %H:%M:%S") if review.reply_time else None,
            "reply_user_id": review.reply_user_id,
            "create_time": review.create_time.strftime("%Y-%m-%d %H:%M:%S") if review.create_time else None
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/admin/{review_id}/reply")
@handle_api_errors("回复评价失败")
def admin_reply_review(
    review_id: int,
    payload: ReviewReplyIn,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """商家/管理员回复评价"""
    from app.models.dish import Dish
    from app.models.canteen import Canteen

    review = db.query(Review).filter(Review.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="评价不存在")

    if current.role == "merchant":
        dish = db.query(Dish).filter(Dish.dish_id == review.dish_id).first()
        if not dish:
            raise HTTPException(status_code=404, detail="评价关联菜品不存在")

        canteen = db.query(Canteen).filter(Canteen.canteen_id == dish.canteen_id).first()
        if not canteen or canteen.merchant_user_id != current.user_id:
            raise HTTPException(status_code=403, detail="无权回复该评价")

    review.reply_content = payload.reply_content.strip()
    review.reply_time = datetime.now()
    review.reply_user_id = current.user_id
    db.commit()
    db.refresh(review)

    return {
        "message": "回复成功",
        "review_id": review.review_id,
        "reply_content": review.reply_content,
        "reply_time": review.reply_time.strftime("%Y-%m-%d %H:%M:%S") if review.reply_time else None,
        "reply_user_id": review.reply_user_id,
    }


@router.delete("/admin/{review_id}")
@handle_api_errors("删除评价失败")
def admin_delete_review(
    review_id: int,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """商家/管理员删除评价"""
    from app.models.dish import Dish
    from app.models.canteen import Canteen

    review = db.query(Review).filter(Review.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="评价不存在")

    if current.role == "merchant":
        dish = db.query(Dish).filter(Dish.dish_id == review.dish_id).first()
        if not dish:
            raise HTTPException(status_code=404, detail="评价关联菜品不存在")

        canteen = db.query(Canteen).filter(Canteen.canteen_id == dish.canteen_id).first()
        if not canteen or canteen.merchant_user_id != current.user_id:
            raise HTTPException(status_code=403, detail="无权删除该评价")
    
    db.delete(review)
    db.commit()
    
    return {"message": "删除成功", "review_id": review_id}
