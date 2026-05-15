from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from api.deps import get_current_user, require_admin
from schemas.product_model import ModelCreate, ModelOut
from services import model_service

router = APIRouter(prefix="/api", tags=["型号管理"])

@router.get("/products/{product_id}/models", response_model=list[ModelOut])
def list_models(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return model_service.get_models_by_product(db, product_id)

@router.post("/models", response_model=ModelOut)
def create_model(data: ModelCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return model_service.create_model(db, data)

@router.delete("/models/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    model_service.delete_model(db, model_id)
    return {"detail": "已删除"}
