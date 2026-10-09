"""
地理位置工具类
使用 Haversine 公式计算两点间距离
"""
import math


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用 Haversine 公式计算两点间距离（单位：米）
    
    Args:
        lat1: 第一个点的纬度
        lon1: 第一个点的经度
        lat2: 第二个点的纬度
        lon2: 第二个点的经度
    
    Returns:
        两点间距离（米）
    """
    # 地球半径（米）
    R = 6371000
    
    # 将角度转换为弧度
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine 公式
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 距离（米）
    distance = R * c
    
    return distance


def format_distance(distance: float) -> str:
    """
    格式化距离显示
    
    Args:
        distance: 距离（米）
    
    Returns:
        格式化后的距离字符串
    """
    if distance < 1000:
        return f"{int(distance)}米"
    else:
        return f"{distance / 1000:.2f}公里"

