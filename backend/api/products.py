from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from api.deps import get_current_user, require_admin
from schemas.product import ProductCreate, ProductUpdate, ProductOut
from services import product_service

router = APIRouter(prefix="/api/products", tags=["产品管理"])

@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return product_service.get_products(db)

@router.post("", response_model=ProductOut)
def create_product(data: ProductCreate, db: Session = Depends(get_db), user=Depends(require_admin)):
    return product_service.create_product(db, data, user.id)

@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return product_service.update_product(db, product_id, data)

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    product_service.delete_product(db, product_id)
    return {"detail": "已删除"}
