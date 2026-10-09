from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.api import deps
from app.crud import coupon as coupon_crud
from app.models.coupon import Coupon, UserCoupon
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponOut, UserCouponOut
from app.utils.pydantic import get_model_data

router = APIRouter(prefix="/coupon", tags=["coupon"])


@router.get("/admin/list", response_model=list[CouponOut])
def list_coupons_admin(
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """获取管理端优惠券列表（包含禁用和未开始的优惠券）"""
    return db.query(Coupon).order_by(Coupon.coupon_id.desc()).all()


@router.get("/detail/{coupon_id}", response_model=CouponOut)
def get_coupon_detail(
    coupon_id: int,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """获取优惠券详情（管理端）"""
    coupon = coupon_crud.coupon.get(db, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    return coupon


@router.get("/list", response_model=list[CouponOut])
def list_coupons(
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """获取可用优惠券列表"""
    return coupon_crud.coupon.list_available(db, current.user_id)


@router.get("/my", response_model=list[UserCouponOut])
def my_coupons(
    status: str = None,  # 支持字符串: "available"(可用), "used"(已使用), "expired"(已过期) 或数字: 0,1,2
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """获取我的优惠券
    
    参数说明：
    - status: 可选，支持以下值：
      - "available" 或 0: 未使用（可用）
      - "used" 或 1: 已使用
      - "expired" 或 2: 已过期
      - 不传或 None: 返回所有优惠券
    """
    # 转换字符串状态为数字
    status_map = {
        "available": 0,
        "used": 1,
        "expired": 2
    }
    
    # 如果是字符串，转换为数字
    if status is not None:
        if isinstance(status, str):
            if status in status_map:
                status_int = status_map[status]
            elif status.isdigit():
                status_int = int(status)
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无效的状态值: {status}，支持的值: available, used, expired, 0, 1, 2"
                )
        else:
            status_int = status
    else:
        status_int = None
    
    return coupon_crud.coupon.get_user_coupons(db, current.user_id, status_int)


@router.post("/claim/{coupon_id}", response_model=UserCouponOut)
def claim_coupon(
    coupon_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """领取优惠券"""
    try:
        return coupon_crud.coupon.claim_coupon(db, current.user_id, coupon_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create", response_model=CouponOut)
def create_coupon(
    payload: CouponCreate,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """创建优惠券（管理端）"""
    coupon = coupon_crud.coupon.create(db, payload)
    return coupon


@router.put("/update/{coupon_id}", response_model=CouponOut)
def update_coupon(
    coupon_id: int,
    payload: CouponUpdate,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """更新优惠券（管理端）"""
    existing = coupon_crud.coupon.get(db, coupon_id)
    if not existing:
        raise HTTPException(status_code=404, detail="优惠券不存在")

    target_type = payload.coupon_type if payload.coupon_type is not None else existing.coupon_type
    target_discount_value = payload.discount_value if payload.discount_value is not None else existing.discount_value
    target_start_time = payload.start_time if payload.start_time is not None else existing.start_time
    target_end_time = payload.end_time if payload.end_time is not None else existing.end_time

    if target_type == "discount" and target_discount_value is not None and Decimal(str(target_discount_value)) > Decimal("10"):
        raise HTTPException(status_code=400, detail="折扣券优惠值请填写 0-10，例如 8 表示 8 折，0.8 表示 8 折")
    if target_end_time <= target_start_time:
        raise HTTPException(status_code=400, detail="失效时间必须晚于生效时间")

    coupon = coupon_crud.coupon.update(db, coupon_id, payload)
    return coupon


@router.put("/status/{coupon_id}")
def update_coupon_status(
    coupon_id: int,
    status: int = Body(..., embed=True),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """更新优惠券状态（管理端）
    
    状态说明：
    - 0: 禁用（前台不可见，后台可见，可恢复）
    - 1: 启用（前台可见，后台可见）
    
    Args:
        coupon_id: 优惠券ID
        status: 状态值（0=禁用，1=启用）
    
    Returns:
        更新后的优惠券信息
    """
    # 验证状态值
    if status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值必须为 0（禁用）或 1（启用）")
    
    # 查询优惠券
    coupon = db.query(Coupon).filter(Coupon.coupon_id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    
    # 更新状态
    old_status = coupon.status
    coupon.status = status
    db.commit()
    db.refresh(coupon)
    
    # 返回结果
    status_text = "启用" if status == 1 else "禁用"
    return {
        "coupon_id": coupon.coupon_id,
        "name": coupon.name,
        "old_status": old_status,
        "status": coupon.status,
        "message": f"优惠券状态已更新为【{status_text}】"
    }


@router.delete("/delete/{coupon_id}")
def delete_coupon(
    coupon_id: int,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """删除优惠券（管理端）
    
    ⚠️ 注意：如果优惠券已被用户领取，将自动先删除关联的领取记录，再删除优惠券。
    如果只是想让优惠券不可见，请使用状态切换接口（PUT /api/coupon/status/{coupon_id}）
    """
    coupon_obj = coupon_crud.coupon.get(db, coupon_id)
    if not coupon_obj:
        raise HTTPException(status_code=404, detail="优惠券不存在")

    try:
        db.query(UserCoupon).filter(UserCoupon.coupon_id == coupon_id).delete(synchronize_session=False)
        db.delete(coupon_obj)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该优惠券已有关联数据，无法删除")

    return {"success": True, "message": "优惠券已删除（无法恢复）"}
