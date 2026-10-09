import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from app.api import deps
from app.crud import dish as dish_crud
from app.storage import media as media_store

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload")
def upload_media(
    file: UploadFile,
    dish_id: int = None,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """上传音视频文件（商家和管理员）
    
    Args:
        file: 上传的文件
        dish_id: 菜品ID（可选）。如果提供，会自动关联到对应菜品
    
    Returns:
        上传后的文件路径
    """
    # 使用 dish_id 或生成唯一标识符（不包含文件名）
    identifier = dish_id if dish_id else f"temp_{current.user_id}"
    path = media_store.save_upload(file, identifier)
    
    # 如果提供了 dish_id，自动关联到菜品
    if dish_id:
        dish = dish_crud.dish.get(db, dish_id)
        if dish:
            media_type = "video" if file.content_type and file.content_type.startswith("video") else "audio"
            dish_crud.dish.update_by_dict(db, dish_id, {"media_path": path, "media_type": media_type})
    
    return {"path": path, "message": "文件上传成功"}


@router.post("/upload/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    target_user_id: int = None,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """上传用户头像
    
    - 普通用户：只能上传自己的头像，target_user_id 会被忽略
    - 管理员：可通过 target_user_id 指定为哪个用户上传头像
    
    支持的图片格式：jpg, jpeg, png, gif, webp
    文件大小限制：5MB
    """
    import os
    
    # 验证文件扩展名
    ext = os.path.splitext(file.filename or "")[1].lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的图片格式: {ext}。支持的格式: jpg, jpeg, png, gif, webp"
        )
    
    # 验证文件大小（限制5MB）
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()  # 获取文件大小
    file.file.seek(0)  # 重置文件指针
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
    
    # 确定实际操作的用户ID：
    # 管理员可指定 target_user_id，普通用户只能操作自己
    is_admin = current.role in ("sys_admin", "canteen_admin", "admin")
    if target_user_id and is_admin:
        actual_user_id = target_user_id
    else:
        actual_user_id = current.user_id
    
    # 保存头像到对应用户目录
    path = media_store.save_upload(file, f"avatar_{actual_user_id}")
    
    # 更新对应用户的头像字段
    from app.crud import user as user_crud
    user_crud.user.update_by_dict(db, actual_user_id, {"avatar": path})
    
    return {
        "path": path,
        "url": f"/uploads/{path}",
        "message": "头像上传成功"
    }


@router.post("/upload/images")
def upload_images(
    files: List[UploadFile] = File(...),
    dish_id: int = None,
    current=Depends(deps.require_merchant),
    db: Session = Depends(deps.get_db)
):
    """上传菜品图片（最多9张，商家和管理员可用）
    
    Args:
        files: 上传的图片文件列表
        dish_id: 菜品ID（可选）。如果提供，会自动关联到对应菜品
    
    Returns:
        上传后的文件路径列表
    """
    # 先验证文件，避免保存时因为空扩展名等问题直接 500
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    for file in files:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片格式: {ext or '未知'}。支持的格式: jpg, jpeg, png, gif, webp"
            )

    # 使用 dish_id 或生成唯一标识符
    identifier = dish_id if dish_id else f"temp_{current.user_id}"
    saved_paths = media_store.save_images(files, identifier)
    
    # 如果提供了 dish_id，自动关联到菜品
    if dish_id:
        dish = dish_crud.dish.get(db, dish_id)
        if dish:
            # 将图片路径保存为JSON
            dish_crud.dish.update_by_dict(db, dish_id, {"images": json.dumps(saved_paths)})
    
    # 返回带 /uploads/ 前缀的完整URL路径
    full_urls = [f"/uploads/{path}" for path in saved_paths]
    
    return {
        "paths": saved_paths,
        "urls": full_urls,
        "count": len(saved_paths), 
        "message": "图片上传成功"
    }


@router.get("/dish/{dish_id}")
def get_dish_media(dish_id: int, db: Session = Depends(deps.get_db)):
    """获取菜品音视频"""
    from pathlib import Path

    dish = dish_crud.dish.get(db, dish_id)
    if not dish or not dish.media_path:
        return {"message": "无媒体"}

    media_path = Path(dish.media_path)
    if not media_path.is_absolute():
        media_path = Path(media_store.get_upload_dir()) / media_path

    if not media_path.exists() or not media_path.is_file():
        raise HTTPException(status_code=404, detail="媒体文件不存在")

    return FileResponse(str(media_path))


@router.get("/dish/{dish_id}/images")
def get_dish_images(dish_id: int, db: Session = Depends(deps.get_db)):
    """获取菜品图片列表"""
    dish = dish_crud.dish.get(db, dish_id)
    if not dish:
        return {"images": []}
    images = media_store.get_image_urls(dish.images)
    return {"images": images}


@router.post("/upload/review")
def upload_review_images_before_create(
    files: List[UploadFile] = File(...),
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """上传评价图片（创建评价前上传，普通用户可用）
    
    用于用户在提交评价前先上传图片，返回图片路径供创建评价时使用
    
    Args:
        files: 上传的图片文件列表（最多9张）
    
    Returns:
        上传后的文件路径列表和完整URL
        
    前端使用示例：
    ```javascript
    // 1. 先上传图片
    const uploadRes = await api.uploadReviewImages(files)
    const imagePaths = uploadRes.paths  // 相对路径列表
    
    // 2. 创建评价时传入图片路径
    await api.createReview({
        order_id: orderId,
        dish_id: dishId,
        rating: 5,
        content: '很好吃',
        images: JSON.stringify(imagePaths)  // 转为JSON字符串
    })
    ```
    """
    import os
    from app.utils.image import convert_to_full_url
    
    # 验证文件数量
    if len(files) > 9:
        raise HTTPException(status_code=400, detail="最多只能上传9张图片")
    
    # 验证每个文件
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    for file in files:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in allowed_exts:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的图片格式: {ext}。支持的格式: jpg, jpeg, png, gif, webp"
            )
        
        # 验证文件大小（限制5MB）
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"文件 {file.filename} 大小不能超过5MB")
    
    # 保存图片，使用用户ID作为标识符
    identifier = f"review_temp_{current.user_id}"
    saved_paths = media_store.save_images(files, identifier)
    
    # 生成完整URL
    full_urls = [convert_to_full_url(path) for path in saved_paths]
    
    return {
        "paths": saved_paths,      # 相对路径（用于存储到数据库）
        "urls": full_urls,          # 完整URL（前端预览用）
        "count": len(saved_paths),
        "message": "图片上传成功"
    }


@router.post("/review/upload")
def upload_review_media(
    review_id: int,
    file: UploadFile,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """上传评价音视频（已创建评价后上传）"""
    from app.crud import review as review_crud
    review = review_crud.review.get(db, review_id)
    if not review or review.user_id != current.user_id:
        raise HTTPException(status_code=404, detail="评价不存在")
    
    path = media_store.save_upload(file, f"review_{review_id}")
    media_type = "video" if file.content_type and file.content_type.startswith("video") else "audio"
    review_crud.review.update_by_dict(db, review_id, {"media_path": path, "media_type": media_type})
    return {"path": path}


@router.post("/review/upload/images")
def upload_review_images(
    review_id: int,
    files: List[UploadFile] = File(...),
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """上传评价图片（已创建评价后上传）"""
    from app.crud import review as review_crud
    
    review = review_crud.review.get(db, review_id)
    if not review or review.user_id != current.user_id:
        raise HTTPException(status_code=404, detail="评价不存在")
    
    saved_paths = media_store.save_images(files, f"review_{review_id}")
    review_crud.review.update_by_dict(db, review_id, {"images": json.dumps(saved_paths)})
    return {"paths": saved_paths, "count": len(saved_paths)}


@router.get("/download/{file_path:path}")
def download_media(file_path: str):
    """下载媒体文件"""
    import os
    from pathlib import Path
    
    # 安全处理：只允许下载uploads目录下的文件
    uploads_dir = Path(media_store.get_upload_dir())
    full_path = uploads_dir / file_path
    
    # 防止路径遍历攻击
    try:
        full_path.resolve().relative_to(uploads_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="无权访问此文件")
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        str(full_path),
        media_type="application/octet-stream",
        filename=full_path.name
    )


@router.get("/stream/{file_path:path}")
def stream_media(file_path: str):
    """流式传输媒体文件（用于视频/音频播放）"""
    import os
    from pathlib import Path
    from fastapi.responses import StreamingResponse
    
    # 安全处理：只允许访问uploads目录下的文件
    uploads_dir = Path(media_store.get_upload_dir())
    full_path = uploads_dir / file_path
    
    # 防止路径遍历攻击
    try:
        full_path.resolve().relative_to(uploads_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="无权访问此文件")
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 根据文件扩展名确定媒体类型
    ext = full_path.suffix.lower()
    media_types = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg"
    }
    media_type = media_types.get(ext, "application/octet-stream")
    
    def iterfile():
        with open(full_path, mode="rb") as file_like:
            yield from file_like
    
    return StreamingResponse(iterfile(), media_type=media_type)

