from sqlalchemy.orm import Session
from fastapi import HTTPException

from db_models.product import Product
from schemas.product import ProductCreate, ProductUpdate

def get_products(db: Session) -> list[Product]:
    return db.query(Product).order_by(Product.created_at.desc()).all()

def create_product(db: Session, data: ProductCreate, user_id: int) -> Product:
    product = Product(name=data.name, description=data.description, created_by=user_id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    if data.name is not None:
        product.name = data.name
    if data.description is not None:
        product.description = data.description
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    db.delete(product)
    db.commit()
