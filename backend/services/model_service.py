from sqlalchemy.orm import Session
from fastapi import HTTPException

from db_models.product_model import ProductModel
from schemas.product_model import ModelCreate

def get_models_by_product(db: Session, product_id: int) -> list[ProductModel]:
    return db.query(ProductModel).filter(ProductModel.product_id == product_id).order_by(ProductModel.created_at.desc()).all()

def create_model(db: Session, data: ModelCreate) -> ProductModel:
    model = ProductModel(product_id=data.product_id, name=data.name, description=data.description)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model

def delete_model(db: Session, model_id: int):
    model = db.query(ProductModel).filter(ProductModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="型号不存在")
    db.delete(model)
    db.commit()
