from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.api import deps
from app.crud import user as user_crud
from app.schemas.user import (
    UserOut,
    UserUpdate,
    UserStatusUpdate,
    UserRoleUpdate,
    UserBatchDelete,
    UserBatchUpdate,
    UserAdminListItem,
    UserAdminListResponse,
    UserAdminPageData,
    UserDetailOut,
    UserDetailResponse,
)
from app.schemas.common import APIResponse
from app.models.user import User
from app.models.order import Order
from app.models.canteen import Canteen

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/info", response_model=UserOut)
def get_user_info(current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    return current


@router.put("/info", response_model=UserOut)
def update_user_info(payload: UserUpdate, current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    user = user_crud.user.update(db, current.user_id, payload)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.get("/list", response_model=UserAdminListResponse)
def list_users(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: str | None = Query(None, description="搜索关键词（用户名、昵称、手机号、学号）"),
    role: str | None = Query(None, description="角色筛选"),
    status: int | None = Query(None, ge=0, le=1, description="状态筛选：0-禁用，1-启用"),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db),
):
    order_count_subquery = db.query(
        Order.user_id,
        func.count(Order.order_id).label("order_count")
    ).group_by(Order.user_id).subquery()

    merchant_canteen_subquery = db.query(
        Canteen.merchant_user_id.label("merchant_user_id"),
        func.min(Canteen.canteen_id).label("canteen_id")
    ).filter(
        Canteen.merchant_user_id.isnot(None)
    ).group_by(
        Canteen.merchant_user_id
    ).subquery()

    query = db.query(
        User,
        func.coalesce(order_count_subquery.c.order_count, 0),
        Canteen.canteen_id,
        Canteen.canteen_name,
    ).outerjoin(
        order_count_subquery, User.user_id == order_count_subquery.c.user_id
    ).outerjoin(
        merchant_canteen_subquery, User.user_id == merchant_canteen_subquery.c.merchant_user_id
    ).outerjoin(
        Canteen, Canteen.canteen_id == merchant_canteen_subquery.c.canteen_id
    )

    if keyword:
        query = query.filter(
            or_(
                User.username.like(f"%{keyword}%"),
                User.nickname.like(f"%{keyword}%"),
                User.student_no.like(f"%{keyword}%"),
                User.phone.like(f"%{keyword}%"),
            )
        )

    if role:
        query = query.filter(User.role == role)

    if status is not None:
        query = query.filter(User.status == status)

    total = query.count()
    rows = query.order_by(User.user_id.desc()).offset((pageNum - 1) * pageSize).limit(pageSize).all()

    records = [
        {
            "user_id": user.user_id,
            "username": user.username,
            "phone": user.phone,
            "email": user.email,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "gender": user.gender,
            "student_no": user.student_no,
            "department": user.department,
            "role": user.role,
            "status": user.status,
            "create_time": user.create_time,
            "update_time": user.update_time,
            "order_count": int(order_count or 0),
            "last_login_time": None,
            "canteen": (
                {
                    "canteen_id": canteen_id,
                    "canteen_name": canteen_name,
                }
                if canteen_id else None
            ),
        }
        for user, order_count, canteen_id, canteen_name in rows
    ]

    return APIResponse.success(
        UserAdminPageData.create(records=records, total=total, page_num=pageNum, page_size=pageSize)
    )


@router.get("/detail/{user_id}", response_model=UserDetailResponse)
def get_user_detail(user_id: int, current=Depends(deps.require_admin), db: Session = Depends(deps.get_db)):
    user = user_crud.user.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    order_count = db.query(func.count(Order.order_id)).filter(Order.user_id == user_id).scalar() or 0
    return APIResponse.success(
        UserDetailOut(
            user_id=user.user_id,
            username=user.username,
            phone=user.phone,
            email=user.email,
            nickname=user.nickname,
            avatar=user.avatar,
            gender=user.gender,
            student_no=user.student_no,
            department=user.department,
            role=user.role,
            status=user.status,
            create_time=user.create_time,
            update_time=user.update_time,
            order_count=int(order_count),
            last_login_time=None,
        )
    )


@router.put("/update/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, current=Depends(deps.require_admin), db: Session = Depends(deps.get_db)):
    user = user_crud.user.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user = user_crud.user.update(db, user_id, payload)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/status/{user_id}", response_model=UserOut)
def update_user_status(user_id: int, payload: UserStatusUpdate, current=Depends(deps.require_admin), db: Session = Depends(deps.get_db)):
    if payload.status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值必须为 0（禁用）或 1（启用）")

    target_user = user_crud.user.get(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user_id == current.user_id and payload.status == 0:
        raise HTTPException(status_code=400, detail="当前登录管理员不能禁用自己")
    if target_user.role == "admin" and current.role != "admin":
        raise HTTPException(status_code=403, detail="只有超级管理员可以修改超级管理员状态")

    user = user_crud.user.update_status(db, user_id, payload.status)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/role/{user_id}", response_model=UserOut)
def update_user_role(user_id: int, payload: UserRoleUpdate, current=Depends(deps.require_admin), db: Session = Depends(deps.get_db)):
    user = user_crud.user.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user_id == current.user_id:
        raise HTTPException(status_code=400, detail="当前登录管理员不能修改自己的角色")
    if user.role == "admin" and current.role != "admin":
        raise HTTPException(status_code=403, detail="只有超级管理员可以修改超级管理员角色")

    role_value = payload.role.value if hasattr(payload.role, "value") else str(payload.role)
    user = user_crud.user.update_role(db, user_id, role_value)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/change-password")
def change_password(old_password: str, new_password: str, current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    from app.core.security import verify_password

    user = user_crud.user.get(db, current.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not verify_password(old_password, user.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    user = user_crud.user.update_password(db, current.user_id, new_password)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"success": True, "message": "密码修改成功"}


@router.delete("/{user_id}")
def delete_user(user_id: int, current=Depends(deps.require_admin), db: Session = Depends(deps.get_db)):
    if user_id == current.user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    user = user_crud.user.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == "admin" and current.role != "admin":
        raise HTTPException(status_code=403, detail="只有超级管理员可以删除超级管理员")

    try:
        success = user_crud.user.delete(db, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除失败")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

    return {"success": True, "message": "用户删除成功"}
