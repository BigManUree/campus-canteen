"""
图片URL处理工具函数
用于将相对路径转换为完整URL
"""
import json
from typing import Optional, List, Union
from app.core.config import get_settings

settings = get_settings()


def convert_to_full_url(path: Optional[str]) -> Optional[str]:
    """将相对路径转换为完整URL
    
    Args:
        path: 图片相对路径或完整URL
        
    Returns:
        完整的图片URL，如果输入为空则返回None
    """
    if not path:
        return None
    
    # 如果已经是完整URL，直接返回
    if path.startswith(('http://', 'https://')):
        return path
    
    # 转换相对路径为完整URL
    if path.startswith('/uploads/'):
        return f"{settings.base_url}{path}"
    elif path.startswith('/'):
        return f"{settings.base_url}/uploads{path}"
    else:
        return f"{settings.base_url}/uploads/{path}"


def convert_images_to_full_urls(images: Optional[Union[str, List[str]]]) -> List[str]:
    """将图片列表（JSON字符串或列表）转换为完整URL列表
    
    Args:
        images: 图片路径的JSON字符串或列表
        
    Returns:
        完整URL的列表
    """
    if not images:
        return []
    
    try:
        # 如果是字符串，尝试解析JSON
        if isinstance(images, str):
            image_paths = json.loads(images)
        else:
            image_paths = images
        
        # 确保是列表
        if not isinstance(image_paths, list):
            return []
        
        # 转换每个路径为完整URL
        return [convert_to_full_url(path) for path in image_paths if path]
    
    except (json.JSONDecodeError, TypeError):
        return []


def get_first_image_url(images: Optional[Union[str, List[str]]]) -> Optional[str]:
    """获取第一张图片的完整URL
    
    Args:
        images: 图片路径的JSON字符串或列表
        
    Returns:
        第一张图片的完整URL，如果没有图片则返回None
    """
    urls = convert_images_to_full_urls(images)
    return urls[0] if urls else None

