"""
Pydantic 工具函数
用于处理 Pydantic v1 和 v2 的兼容性问题
"""
from typing import Any
from pydantic import BaseModel


def get_model_data(obj_in: BaseModel, exclude_unset: bool = True, **kwargs) -> dict[str, Any]:
    """
    从 Pydantic 模型中提取数据，兼容 v1 和 v2
    
    Args:
        obj_in: Pydantic 模型实例
        exclude_unset: 是否排除未设置的字段
        **kwargs: 传递给 model_dump 的其他参数（如 exclude, mode 等）
        
    Returns:
        dict: 模型数据字典
    """
    try:
        return obj_in.model_dump(exclude_unset=exclude_unset, **kwargs)
    except (AttributeError, TypeError):
        # Pydantic v1 或参数不支持
        try:
            # 尝试移除 v2 特有的参数
            v1_kwargs = {k: v for k, v in kwargs.items() if k != "mode"}
            return obj_in.dict(exclude_unset=exclude_unset, **v1_kwargs)
        except AttributeError:
            # 完全回退到 v1
            return obj_in.dict(exclude_unset=exclude_unset)

