from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api import deps
from app.models.canteen import Canteen
from app.utils.geo import calculate_distance, format_distance

router = APIRouter(prefix="/location", tags=["location"])


@router.get("/canteen/{canteen_id}")
def canteen_location(
    canteen_id: int,
    user_lat: Optional[float] = Query(None, description="用户纬度"),
    user_lon: Optional[float] = Query(None, description="用户经度"),
    db: Session = Depends(deps.get_db)
):
    """获取档口位置信息，可选计算距离"""
    c = db.query(Canteen).filter(Canteen.canteen_id == canteen_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="档口不存在")
    
    result = {
        "canteenId": c.canteen_id,
        "name": c.canteen_name,
        "latitude": float(c.latitude) if c.latitude is not None else None,
        "longitude": float(c.longitude) if c.longitude is not None else None,
        "address": c.address,
    }
    
    # 如果提供了用户位置，计算距离
    if user_lat and user_lon and c.latitude and c.longitude:
        distance = calculate_distance(
            float(user_lat),
            float(user_lon),
            float(c.latitude),
            float(c.longitude)
        )
        result["distance"] = distance
        result["distanceText"] = format_distance(distance)
    
    return result


@router.get("/pickup")
def list_pickup_points(db: Session = Depends(deps.get_db)):
    """获取所有自提点列表"""
    canteens = db.query(Canteen).filter(
        Canteen.status == 1,
        Canteen.latitude.isnot(None),
        Canteen.longitude.isnot(None)
    ).all()
    
    return [
        {
            "canteenId": c.canteen_id,
            "name": c.canteen_name,
            "building": c.building,
            "floor": c.floor,
            "windowNo": c.window_no,
            "latitude": float(c.latitude),
            "longitude": float(c.longitude),
            "address": c.address,
        }
        for c in canteens
    ]


@router.get("/distance")
def calculate_distance_api(
    lat1: float = Query(..., description="第一个点的纬度"),
    lon1: float = Query(..., description="第一个点的经度"),
    lat2: float = Query(..., description="第二个点的纬度"),
    lon2: float = Query(..., description="第二个点的经度")
):
    """计算两点间距离（独立接口）"""
    distance = calculate_distance(lat1, lon1, lat2, lon2)
    return {
        "distance": distance,
        "distanceText": format_distance(distance),
        "unit": "米"
    }

