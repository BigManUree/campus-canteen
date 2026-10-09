from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import cart as cart_crud
from app.schemas.cart import CartItemIn, CartItemOut, CartItemUpdate

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/list", response_model=list[CartItemOut])
def list_cart(current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    return cart_crud.cart.list_by_user(db, current.user_id)


@router.post("/add", response_model=CartItemOut)
def add_cart_item(
    payload: CartItemIn,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    try:
        return cart_crud.cart.add_or_update(db, current.user_id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="菜品不存在或已下架")


@router.put("/update/{item_id}", response_model=CartItemOut)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """更新购物车商品数量或备注
    
    修复：避免重复更新，只使用 CRUD 方法
    """
    item = cart_crud.cart.get_user_item(db, current.user_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="购物车商品不存在")
    
    # 验证数量
    if payload.quantity is not None and payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="数量必须大于0")
    
    # 使用 CRUD 方法更新
    updated_item = cart_crud.cart.update(db, item_id, payload)
    if not updated_item:
        raise HTTPException(status_code=404, detail="更新失败")
    
    return updated_item


@router.delete("/remove/{item_id}")
def remove_cart_item(
    item_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    item = cart_crud.cart.get_user_item(db, current.user_id, item_id)
    if item:
        cart_crud.cart.delete(db, item_id)
    return {"success": True}


