from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc
from typing import Optional
from pydantic import BaseModel

from app.api import deps
from app.models.user import User
from app.models.dish import Dish
from app.models.canteen import Canteen
from app.models.search_history import SearchHistory, HotSearch

router = APIRouter()


class AddHistoryRequest(BaseModel):
    keyword: str
    search_type: str = "all"


@router.get("/all")
def search_all(
    keyword: str = Query(..., description="搜索关键词"),
    type: str = Query("all", description="搜索类型：dish/canteen/all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional)
):
    """
    综合搜索接口
    """
    # 记录搜索历史
    if current_user:
        try:
            history = SearchHistory(
                user_id=current_user.user_id,
                keyword=keyword,
                search_type=type
            )
            db.add(history)
            
            # 更新热门搜索
            hot = db.query(HotSearch).filter(HotSearch.keyword == keyword).first()
            if hot:
                hot.search_count += 1
            else:
                hot = HotSearch(keyword=keyword, search_count=1)
                db.add(hot)
            
            db.commit()
        except:
            db.rollback()
    else:
        try:
            hot = db.query(HotSearch).filter(HotSearch.keyword == keyword).first()
            if hot:
                hot.search_count += 1
            else:
                hot = HotSearch(keyword=keyword, search_count=1)
                db.add(hot)
            db.commit()
        except:
            db.rollback()
    
    result = {
        "dishes": [],
        "canteens": [],
        "total": 0,
        "has_more": False
    }
    
    # 搜索菜品
    if type in ["all", "dish"]:
        dishes_query = db.query(
            Dish.dish_id,
            Dish.name,
            Dish.price,
            Dish.images,
            Dish.description,
            Dish.canteen_id,
            Canteen.canteen_name,
            Dish.view_count,
            Dish.favorite_count
        ).join(
            Canteen, Dish.canteen_id == Canteen.canteen_id
        ).filter(
            Dish.status == 1,
            or_(
                Dish.name.like(f"%{keyword}%"),
                Dish.description.like(f"%{keyword}%")
            )
        )
        
        total_dishes = dishes_query.count()
        dishes = dishes_query.offset((page - 1) * page_size).limit(page_size).all()
        
        result["dishes"] = [
            {
                "dish_id": d.dish_id,
                "name": d.name,
                "price": float(d.price),
                "images": d.images or "",
                "description": d.description or "",
                "canteen_id": d.canteen_id,
                "canteen_name": d.canteen_name,
                "sales_count": d.view_count or 0,
                "rating": 4.5  # 暂时固定，后续可从评论计算
            }
            for d in dishes
        ]
        result["total"] += total_dishes
    
    # 搜索档口/食堂
    if type in ["all", "canteen"]:
        canteens_query = db.query(Canteen).filter(
            Canteen.status == 1,
            or_(
                Canteen.canteen_name.like(f"%{keyword}%"),
                Canteen.building.like(f"%{keyword}%"),
                Canteen.address.like(f"%{keyword}%")
            )
        )
        
        total_canteens = canteens_query.count()
        canteens = canteens_query.offset((page - 1) * page_size).limit(page_size).all()
        
        result["canteens"] = [
            {
                "canteen_id": c.canteen_id,
                "canteen_name": c.canteen_name,
                "image": "",  # 食堂暂无图片字段
                "building": c.building,
                "floor": c.floor or "",
                "description": f"{c.building}{c.floor or ''} {c.window_no or ''}"
            }
            for c in canteens
        ]
        result["total"] += total_canteens
    
    # 判断是否有更多
    result["has_more"] = result["total"] > page * page_size
    
    return result


@router.get("/suggest")
def search_suggest(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(deps.get_db)
):
    """
    搜索建议接口
    """
    suggestions = []
    
    # 从菜品中获取建议
    dishes = db.query(
        Dish.name,
        func.count(Dish.dish_id).label("count")
    ).filter(
        Dish.status == 1,
        Dish.name.like(f"%{keyword}%")
    ).group_by(Dish.name).limit(limit // 2).all()
    
    for dish in dishes:
        suggestions.append({
            "text": dish.name,
            "type": "dish",
            "count": dish.count
        })
    
    # 从食堂中获取建议
    canteens = db.query(
        Canteen.canteen_name,
        func.count(Canteen.canteen_id).label("count")
    ).filter(
        Canteen.status == 1,
        Canteen.canteen_name.like(f"%{keyword}%")
    ).group_by(Canteen.canteen_name).limit(limit // 2).all()
    
    for canteen in canteens:
        suggestions.append({
            "text": canteen.canteen_name,
            "type": "canteen",
            "count": canteen.count
        })
    
    # 从热门搜索中获取建议
    hot_keywords = db.query(HotSearch).filter(
        HotSearch.keyword.like(f"%{keyword}%")
    ).order_by(desc(HotSearch.search_count)).limit(limit // 2).all()
    
    for hot in hot_keywords:
        suggestions.append({
            "text": hot.keyword,
            "type": "keyword",
            "count": hot.search_count
        })
    
    # 去重并限制数量
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s["text"] not in seen:
            seen.add(s["text"])
            unique_suggestions.append(s)
            if len(unique_suggestions) >= limit:
                break
    
    return {"suggestions": unique_suggestions}


@router.get("/hot")
def get_hot_search(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(deps.get_db)
):
    """
    热门搜索接口
    """
    hot_list = db.query(HotSearch).order_by(
        desc(HotSearch.search_count)
    ).limit(limit).all()
    
    keywords = [
        {
            "keyword": hot.keyword,
            "count": hot.search_count,
            "rank": idx + 1
        }
        for idx, hot in enumerate(hot_list)
    ]
    
    return {"keywords": keywords}


@router.get("/history")
def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取搜索历史
    """
    history = db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.user_id
    ).order_by(desc(SearchHistory.create_time)).limit(limit).all()
    
    # 去重，保留最新的
    seen = set()
    unique_history = []
    for h in history:
        if h.keyword not in seen:
            seen.add(h.keyword)
            unique_history.append({
                "keyword": h.keyword,
                "search_type": h.search_type,
                "create_time": h.create_time.isoformat()
            })
    
    return {"history": unique_history}


@router.post("/history")
def add_search_history(
    request: AddHistoryRequest = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    添加搜索历史
    请求体格式：{"keyword": "宫保鸡丁", "search_type": "dish"}
    """
    history = SearchHistory(
        user_id=current_user.user_id,
        keyword=request.keyword,
        search_type=request.search_type
    )
    db.add(history)
    db.commit()
    
    return {"message": "添加成功"}


@router.delete("/history")
def clear_search_history(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    清空搜索历史
    """
    db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.user_id
    ).delete()
    db.commit()
    
    return {"message": "清空成功"}

