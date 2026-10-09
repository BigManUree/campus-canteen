from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.api.decorators import handle_api_errors
from app.crud import address as address_crud
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate

router = APIRouter(prefix="/address", tags=["address"])


@router.get("/list", response_model=list[AddressOut])
@handle_api_errors("获取地址列表失败")
def list_addresses(current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    return address_crud.address.list_by_user(db, current.user_id)


@router.post("/create", response_model=AddressOut)
@handle_api_errors("创建地址失败")
def create_address(
    payload: AddressCreate,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    return address_crud.address.create_for_user(db, current.user_id, payload)


@router.put("/update/{address_id}", response_model=AddressOut)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    addr = address_crud.address.get_user_address(db, current.user_id, address_id)
    if not addr:
        raise HTTPException(status_code=404, detail="地址不存在")
    return address_crud.address.update_for_user(db, current.user_id, addr, payload)


@router.delete("/delete/{address_id}")
def delete_address(
    address_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    addr = address_crud.address.get_user_address(db, current.user_id, address_id)
    if not addr:
        raise HTTPException(status_code=404, detail="地址不存在")
    address_crud.address.delete(db, address_id)
    return {"success": True}


