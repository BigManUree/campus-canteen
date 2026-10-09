from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from sqlalchemy.orm import Session

from app.api import deps
from app.api.decorators import handle_api_errors
from app.crud import activity as activity_crud
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityOut
from app.utils.activity import parse_activity_json, prepare_activity_update_data
from app.storage import media as media_store

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/list", response_model=list[ActivityOut])
@handle_api_errors("获取活动列表失败")
def list_activities(
    current=Depends(deps.get_current_user_optional),
    db: Session = Depends(deps.get_db)
):
    query = db.query(Activity)
    if not (current and current.role in ["admin", "merchant", "sys_admin", "canteen_admin"]):
        query = query.filter(Activity.status == 1)
    activities = query.order_by(Activity.sort_order.desc(), Activity.start_time.desc(), Activity.activity_id.desc()).all()
    return [parse_activity_json(act) for act in activities]


@router.get("/admin/list", response_model=list[ActivityOut])
@handle_api_errors("获取活动列表失败")
def admin_list_activities(
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    activities = db.query(Activity).order_by(Activity.sort_order.desc(), Activity.start_time.desc(), Activity.activity_id.desc()).all()
    return [parse_activity_json(act) for act in activities]


@router.get("/detail/{activity_id}", response_model=ActivityOut)
def get_activity_detail(
    activity_id: int,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    activity = activity_crud.activity.get(db, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    return parse_activity_json(activity)


@router.post("/create", response_model=ActivityOut)
def create_activity(
    payload: ActivityCreate,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    activity = activity_crud.activity.create(db, payload)
    return parse_activity_json(activity)


@router.put("/update/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    from app.utils.pydantic import get_model_data

    update_data = prepare_activity_update_data(get_model_data(payload))
    activity = activity_crud.activity.update_by_dict(db, activity_id, update_data)
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    return parse_activity_json(activity)


@router.put("/status/{activity_id}")
def update_activity_status(
    activity_id: int,
    status: int = Body(..., embed=True),
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    if status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值必须为 0（下线）或 1（发布）")

    activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    activity.status = status
    activity.update_time = datetime.now()
    db.commit()
    db.refresh(activity)

    return {
        "activity_id": activity.activity_id,
        "title": activity.title,
        "status": activity.status,
        "message": f"活动已{'发布' if status == 1 else '下线'}"
    }


@router.delete("/delete/{activity_id}")
def delete_activity(
    activity_id: int,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    activity = activity_crud.activity.get(db, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    success = activity_crud.activity.delete(db, activity_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")

    return {"success": True, "message": "活动已删除"}


@router.post("/upload/image")
def upload_activity_image(
    file: UploadFile = File(...),
    activity_id: int = None,
    current=Depends(deps.require_admin),
    db: Session = Depends(deps.get_db)
):
    import os

    ext = os.path.splitext(file.filename or "")[1].lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="仅支持 jpg、jpeg、png、gif、webp 格式")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")

    identifier = f"activity_{activity_id}" if activity_id else f"activity_temp_{current.user_id}"
    path = media_store.save_upload(file, identifier)

    if activity_id:
        activity = activity_crud.activity.get(db, activity_id)
        if not activity:
            raise HTTPException(status_code=404, detail="活动不存在")
        activity_crud.activity.update_by_dict(db, activity_id, {"cover_image": path})

    return {
        "path": path,
        "url": f"/uploads/{path}",
        "message": "图片上传成功"
    }
