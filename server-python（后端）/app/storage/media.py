import os
import json
from pathlib import Path
from typing import List

from fastapi import HTTPException, UploadFile

from app.core.config import get_settings

settings = get_settings()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIGURED_UPLOAD_DIR = Path(settings.media_upload_path)
FIXED_UPLOAD_DIR = (
    CONFIGURED_UPLOAD_DIR if CONFIGURED_UPLOAD_DIR.is_absolute() else (PROJECT_ROOT / CONFIGURED_UPLOAD_DIR)
).resolve()


def _get_base_upload_dir() -> Path:
    """获取固定上传目录，统一保存到项目根目录下的 uploads。"""
    try:
        FIXED_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        test_file = FIXED_UPLOAD_DIR / ".write_test"
        with test_file.open("wb") as f:
            f.write(b"ok")
        test_file.unlink(missing_ok=True)
        return FIXED_UPLOAD_DIR
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传目录不可写: {FIXED_UPLOAD_DIR} - {e}")


def save_upload(file: UploadFile, identifier) -> str:
    """保存音视频文件或图片文件
    
    Args:
        file: 上传的文件
        identifier: 标识符（可以是 dish_id、用户ID 或其他字符串，作为目录名）
    
    Returns:
        保存后的文件路径
    """
    import time
    import hashlib
    
    ext = os.path.splitext(file.filename or "")[1].lower()
    
    # 支持音视频和图片格式
    allowed_media = {".mp4", ".mov", ".mp3", ".wav", ".avi", ".ogg"}
    allowed_images = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    allowed = allowed_media | allowed_images
    
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
    
    # 确保基础上传目录存在
    base_upload_dir = _get_base_upload_dir()
    
    # 创建目标子目录（identifier 作为目录名）
    target_dir = base_upload_dir / str(identifier)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise HTTPException(
            status_code=500, 
            detail=f"无法创建目录 {target_dir}，请检查目录权限"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"创建目录失败: {str(e)}"
        )
    
    # 生成安全的文件名（避免中文和特殊字符导致的问题）
    # 使用时间戳 + 原文件名的哈希值，保留原扩展名
    timestamp = int(time.time() * 1000)  # 毫秒级时间戳
    original_name = file.filename or "file"
    name_hash = hashlib.md5(original_name.encode('utf-8')).hexdigest()[:8]
    safe_filename = f"{timestamp}_{name_hash}{ext}"
    
    target_path = target_dir / safe_filename
    
    # 保存文件
    try:
        with target_path.open("wb") as f:
            f.write(file.file.read())
    except PermissionError:
        raise HTTPException(
            status_code=500, 
            detail=f"无法写入文件 {target_path}，请检查目录权限"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"保存文件失败: {str(e)}"
        )
    
    # 返回相对于 uploads 目录的路径
    relative_path = target_path.relative_to(base_upload_dir)
    return str(relative_path).replace("\\", "/")


def save_images(files: List[UploadFile], identifier) -> List[str]:
    """保存图片文件（最多9张）
    
    Args:
        files: 上传的图片文件列表
        identifier: 标识符（可以是 dish_id 或其他字符串，作为目录名）
    
    Returns:
        保存后的文件路径列表
    """
    import time
    import hashlib
    
    if len(files) > 9:
        raise HTTPException(status_code=400, detail="最多只能上传9张图片")
    
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    saved_paths = []
    
    # 确保基础上传目录存在
    base_upload_dir = _get_base_upload_dir()
    
    # 创建目标子目录
    target_dir = base_upload_dir / str(identifier) / "images"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise HTTPException(
            status_code=500, 
            detail=f"无法创建目录 {target_dir}，请检查目录权限"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"创建目录失败: {str(e)}"
        )
    
    for idx, file in enumerate(files):
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in allowed_exts:
            raise HTTPException(status_code=400, detail=f"图片格式不支持: {ext}")
        
        # 生成安全的文件名（避免中文和特殊字符导致的问题）
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        original_name = file.filename or f"image_{idx}"
        name_hash = hashlib.md5(original_name.encode('utf-8')).hexdigest()[:8]
        safe_filename = f"{idx}_{timestamp}_{name_hash}{ext}"
        
        target_path = target_dir / safe_filename
        
        try:
            with target_path.open("wb") as f:
                f.write(file.file.read())
        except PermissionError:
            raise HTTPException(
                status_code=500, 
                detail=f"无法写入文件 {target_path}，请检查目录权限"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"保存文件失败: {str(e)}"
            )
        
        # 返回相对于 uploads 目录的路径
        relative_path = target_path.relative_to(base_upload_dir)
        saved_paths.append(str(relative_path).replace("\\", "/"))
    
    return saved_paths


def get_image_urls(images_json: str) -> List[str]:
    """从JSON字符串解析图片URL列表"""
    if not images_json:
        return []
    try:
        return json.loads(images_json)
    except:
        return []


def get_upload_dir() -> str:
    """获取上传目录路径"""
    return str(_get_base_upload_dir())

