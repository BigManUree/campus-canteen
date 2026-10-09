from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel

from app.api import deps
from app.crud import canteen as canteen_crud
from app.schemas.canteen import CanteenCreate, CanteenUpdate, CanteenOut
from app.schemas.common import PaginatedResponse

from app.storage import media as media_store

router = APIRouter(prefix="/canteen", tags=["canteen"])


# 批量操作请求模型

class BatchStatusUpdate(BaseModel):
    """批量更新状态请求"""
    canteen_ids: List[int]
    status: int  # 0-禁用，1-启用
    
    class Config:
        json_schema_extra = {
            "example": {
                "canteen_ids": [1, 2, 3],
                "status": 1
            }
        }


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    canteen_ids: List[int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "canteen_ids": [1, 2, 3]
            }
        }


class MerchantStoreSettingsUpdate(BaseModel):
    canteen_name: Optional[str] = None
    name: Optional[str] = None
    avatar: Optional[str] = None
    notice: Optional[str] = None
    notice_enabled: Optional[bool] = None
    phone: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_person: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    business_hours: Optional[str] = None
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    rest_days: Optional[str] = None
    sort_order: Optional[int] = None
    avg_price: Optional[float] = None
    status: Optional[int] = None


@router.get("/my", response_model=CanteenOut)
def get_my_canteen(
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """获取当前商家绑定的食堂信息（商家端）
    
    商家登录后调用此接口获取自己管理的食堂。
    超级管理员调用此接口会返回 403（管理员没有绑定食堂）。
    """
    from app.api.deps import is_merchant_role
    if not is_merchant_role(current.role):
        raise HTTPException(status_code=403, detail="仅商家角色可调用此接口")
    
    from app.models.canteen import Canteen
    canteen = db.query(Canteen).filter(
        Canteen.merchant_user_id == current.user_id
    ).first()
    if not canteen:
        raise HTTPException(status_code=404, detail="您还没有绑定食堂，请联系管理员分配")
    return canteen


@router.put("/merchant/my", response_model=CanteenOut)
def update_my_canteen(
    payload: MerchantStoreSettingsUpdate,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """商家更新自己的店铺设置"""
    from app.api.deps import is_merchant_role
    from app.models.canteen import Canteen

    if not is_merchant_role(current.role):
        raise HTTPException(status_code=403, detail="仅商家角色可调用此接口")

    canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
    if not canteen:
        raise HTTPException(status_code=404, detail="您还没有绑定食堂，请联系管理员分配")

    update_data = {}

    canteen_name = payload.canteen_name if payload.canteen_name is not None else payload.name
    if canteen_name is not None:
        update_data["canteen_name"] = canteen_name.strip()

    if payload.avatar is not None:
        update_data["avatar"] = payload.avatar
    if payload.notice is not None:
        update_data["notice"] = payload.notice
    if payload.notice_enabled is not None:
        update_data["notice_enabled"] = 1 if payload.notice_enabled else 0
    if payload.description is not None:
        update_data["description"] = payload.description
    if payload.contact_person is not None:
        update_data["contact_person"] = payload.contact_person
    if payload.rest_days is not None:
        update_data["rest_days"] = payload.rest_days
    if payload.sort_order is not None:
        update_data["sort_order"] = payload.sort_order

    phone = payload.contact_phone if payload.contact_phone is not None else payload.phone
    if phone is not None:
        update_data["contact_phone"] = phone

    if payload.location is not None:
        update_data["location"] = payload.location
    if payload.business_hours is not None:
        update_data["business_hours"] = payload.business_hours
        update_data["open_time"] = payload.business_hours
    elif payload.open_time is not None:
        update_data["open_time"] = payload.open_time
        update_data["business_hours"] = payload.open_time

    if payload.avg_price is not None:
        update_data["avg_price"] = payload.avg_price
    if payload.status is not None:
        update_data["status"] = payload.status

    if not update_data:
        return canteen

    for field, value in update_data.items():
        setattr(canteen, field, value)

    db.commit()
    db.refresh(canteen)
    return canteen


@router.post("/merchant/upload-avatar")
def upload_my_canteen_avatar(
    file: UploadFile = File(...),
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """商家上传自己店铺头像"""
    from app.api.deps import is_merchant_role
    from app.models.canteen import Canteen
    import os

    if not is_merchant_role(current.role):
        raise HTTPException(status_code=403, detail="仅商家角色可调用此接口")

    canteen = db.query(Canteen).filter(Canteen.merchant_user_id == current.user_id).first()
    if not canteen:
        raise HTTPException(status_code=404, detail="您还没有绑定食堂，请联系管理员分配")

    ext = os.path.splitext(file.filename or "")[1].lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="仅支持 jpg、jpeg、png、gif、webp 图片")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")

    path = media_store.save_upload(file, f"canteens/{canteen.canteen_id}")
    canteen.avatar = path
    db.commit()
    db.refresh(canteen)

    return {
        "path": path,
        "url": f"/uploads/{path}",
        "message": "店铺头像上传成功"
    }


@router.get("/list", response_model=PaginatedResponse[CanteenOut])
def list_canteens(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（食堂名称）"),
    status: Optional[int] = Query(None, description="食堂状态：0=禁用，1=启用，不传则返回所有"),
    db: Session = Depends(deps.get_db)
):
    """获取食堂列表（支持分页、搜索和状态筛选）
    
    ⭐ 新增 status 参数支持：
    - 不传 status：返回所有食堂（启用+禁用）
    - status=1：只返回启用的食堂
    - status=0：只返回禁用的食堂
    
    移除硬编码的 status=1 过滤，支持动态状态筛选
    """
    from app.models.canteen import Canteen
    from app.models.dish import Dish
    from sqlalchemy import or_
    from app.core.logging import logger
    
    # 构建基础查询
    query = db.query(Canteen)
    
    # ⭐⭐⭐ 关键修复：根据 status 参数动态过滤 ⭐⭐⭐
    if status is not None:
        query = query.filter(Canteen.status == status)
        logger.info(f"🔍 [食堂列表] 过滤条件: status={status}")
    else:
        logger.info(f"🔍 [食堂列表] 无状态过滤，返回所有食堂")
    
    # 关键词搜索
    if keyword:
        query = query.filter(Canteen.canteen_name.like(f"%{keyword}%"))
        logger.info(f"🔍 [食堂列表] 关键词搜索: {keyword}")
    
    # 计算总数
    total = query.count()
    logger.info(f"📊 [食堂列表] 过滤后总数: {total}")
    
    # 分页查询
    offset = (page - 1) * page_size
    items = query.order_by(Canteen.create_time.desc()).offset(offset).limit(page_size).all()
    logger.info(f"📦 [食堂列表] 返回数据: {len(items)} 条")

    canteen_ids = [item.canteen_id for item in items]
    window_count_map = {}
    if canteen_ids:
        window_count_rows = (
            db.query(Dish.canteen_id, func.count(func.distinct(Dish.window_id)))
            .filter(Dish.canteen_id.in_(canteen_ids), Dish.status == 1, Dish.window_id.isnot(None))
            .group_by(Dish.canteen_id)
            .all()
        )
        window_count_map = {canteen_id: count for canteen_id, count in window_count_rows}

    response_items = []
    for item in items:
        item_dict = {column.name: getattr(item, column.name) for column in item.__table__.columns}
        item_dict["window_count"] = window_count_map.get(item.canteen_id, 0)
        response_items.append(item_dict)
    
    # 调试日志：输出返回的食堂状态
    if items:
        for item in items[:5]:  # 只输出前5条，避免日志过多
            logger.info(f"  - {item.canteen_name} (ID: {item.canteen_id}, status: {item.status})")
        if len(items) > 5:
            logger.info(f"  ... 还有 {len(items) - 5} 条数据")
    
    return PaginatedResponse.create(items=response_items, total=total, page=page, page_size=page_size)


@router.get("/detail/{canteen_id}", response_model=CanteenOut)
def canteen_detail(canteen_id: int, db: Session = Depends(deps.get_db)):
    """获取食堂详情"""
    canteen = canteen_crud.canteen.get(db, canteen_id)
    if not canteen:
        raise HTTPException(status_code=404, detail="食堂不存在")
    return canteen


@router.post("/assign-merchant/{canteen_id}")
def assign_merchant_to_canteen(
    canteen_id: int,
    merchant_user_id: int,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """将商家账号绑定到食堂（超级管理员操作）
    
    Args:
        canteen_id: 食堂ID
        merchant_user_id: 要绑定的商家用户ID
    """
    from app.models.canteen import Canteen
    from app.models.user import User
    
    canteen = db.query(Canteen).filter(Canteen.canteen_id == canteen_id).first()
    if not canteen:
        raise HTTPException(status_code=404, detail="食堂不存在")
    
    merchant = db.query(User).filter(User.user_id == merchant_user_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="用户不存在")
    if merchant.role not in ("merchant", "canteen_admin"):
        raise HTTPException(status_code=400, detail="该用户不是商家角色，请先将其角色设置为商家")

    db.query(Canteen).filter(
        Canteen.merchant_user_id == merchant_user_id,
        Canteen.canteen_id != canteen_id
    ).update({"merchant_user_id": None}, synchronize_session=False)
    
    canteen.merchant_user_id = merchant_user_id
    db.commit()
    db.refresh(canteen)
    
    return {
        "success": True,
        "message": f"已将用户 {merchant.nickname or merchant.username} 绑定到食堂 {canteen.canteen_name}",
        "canteen_id": canteen_id,
        "merchant_user_id": merchant_user_id
    }


@router.post("/create", response_model=CanteenOut)
def create_canteen(
    payload: CanteenCreate,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """创建食堂（管理端）"""
    return canteen_crud.canteen.create(db, payload)


@router.put("/update/{canteen_id}", response_model=CanteenOut)
def update_canteen(
    canteen_id: int,
    payload: CanteenUpdate,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """更新食堂信息（管理端）"""
    canteen = canteen_crud.canteen.update(db, canteen_id, payload)
    if not canteen:
        raise HTTPException(status_code=404, detail="食堂不存在")
    return canteen


@router.put("/status/{canteen_id}", response_model=CanteenOut)
def update_canteen_status(
    canteen_id: int,
    status: int = Query(..., ge=0, le=1, description="状态：0-禁用，1-启用"),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """更新食堂状态（管理端）"""
    canteen = canteen_crud.canteen.update_status(db, canteen_id, status)
    if not canteen:
        raise HTTPException(status_code=404, detail="食堂不存在")
    return canteen


@router.delete("/delete/{canteen_id}")
def delete_canteen(
    canteen_id: int,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """删除食堂（管理端）- 级联删除所有相关数据"""
    try:
        success = canteen_crud.canteen.delete_with_cascade(db, canteen_id)
        if not success:
            raise HTTPException(status_code=404, detail="食堂不存在")
        return {"success": True, "message": "食堂及相关数据已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ==================== 批量操作接口 ====================

@router.post("/batch/status")
async def batch_update_status(
    payload: BatchStatusUpdate,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """✅ 批量更新食堂状态（管理端）
    
    一次请求更新多个食堂的状态，提升操作效率
    
    Args:
        payload: 批量更新请求
            - canteen_ids: 食堂ID列表
            - status: 目标状态（0-禁用，1-启用）
    
    Returns:
        {
            "success": true,
            "success_count": 3,
            "failed_count": 0,
            "failed_items": []
        }
    
    前端使用示例：
    ```javascript
    // 批量启用食堂
    const result = await api.batchUpdateCanteenStatus({
        canteen_ids: [1, 2, 3],
        status: 1
    })
    
    console.log(`成功更新 ${result.success_count} 个食堂`)
    ```
    """
    if not payload.canteen_ids:
        raise HTTPException(status_code=400, detail="食堂ID列表不能为空")
    
    if len(payload.canteen_ids) > 100:
        raise HTTPException(status_code=400, detail="单次最多更新100个食堂")
    
    if payload.status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值必须为 0（禁用）或 1（启用）")
    
    success_count = 0
    failed_items = []
    
    for canteen_id in payload.canteen_ids:
        try:
            canteen = canteen_crud.canteen.update_status(db, canteen_id, payload.status)
            if canteen:
                success_count += 1
            else:
                failed_items.append({
                    "canteen_id": canteen_id,
                    "reason": "食堂不存在"
                })
        except Exception as e:
            failed_items.append({
                "canteen_id": canteen_id,
                "reason": str(e)
            })
    
    return {
        "success": True,
        "success_count": success_count,
        "failed_count": len(failed_items),
        "failed_items": failed_items,
        "message": f"成功更新 {success_count} 个食堂状态"
    }


@router.post("/batch/delete")
def batch_delete_canteens(
    payload: BatchDeleteRequest,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    """✅ 批量删除食堂（管理端）
    
    一次请求删除多个食堂及其相关数据，提升操作效率
    
    ⚠️ 警告：此操作会级联删除食堂的所有相关数据：
    - 食堂下的所有菜品
    - 食堂的所有评价
    - 食堂的排队信息
    - 购物车中的相关菜品
    - 收藏中的相关菜品
    - 订单项中的相关菜品
    - 相关订单会被标记为已取消
    
    Args:
        payload: 批量删除请求
            - canteen_ids: 食堂ID列表
    
    Returns:
        {
            "success": true,
            "success_count": 3,
            "failed_count": 0,
            "failed_items": []
        }
    
    前端使用示例：
    ```javascript
    // 批量删除食堂
    const result = await api.batchDeleteCanteens({
        canteen_ids: [1, 2, 3]
    })
    
    if (result.success_count > 0) {
        console.log(`成功删除 ${result.success_count} 个食堂`)
    }
    
    if (result.failed_count > 0) {
        console.log('删除失败的食堂:', result.failed_items)
    }
    ```
    """
    if not payload.canteen_ids:
        raise HTTPException(status_code=400, detail="食堂ID列表不能为空")
    
    if len(payload.canteen_ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多删除50个食堂")
    
    success_count = 0
    failed_items = []
    
    for canteen_id in payload.canteen_ids:
        try:
            success = canteen_crud.canteen.delete_with_cascade(db, canteen_id)
            if success:
                success_count += 1
            else:
                failed_items.append({
                    "canteen_id": canteen_id,
                    "reason": "食堂不存在"
                })
        except Exception as e:
            db.rollback()  # 回滚当前食堂的删除操作
            failed_items.append({
                "canteen_id": canteen_id,
                "reason": str(e)
            })
    
    return {
        "success": True,
        "success_count": success_count,
        "failed_count": len(failed_items),
        "failed_items": failed_items,
        "message": f"成功删除 {success_count} 个食堂"
    }

