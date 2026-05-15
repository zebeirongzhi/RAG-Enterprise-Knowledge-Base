from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from api.deps import require_admin
from schemas.user import UserOut, UserUpdateRole, UserCreate
from services import user_service

router = APIRouter(prefix="/api/users", tags=["用户管理"])

@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_service.get_users(db)

@router.post("", response_model=UserOut)
def add_user(data: UserCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_service.create_user(db, data.username, data.password, data.role)

@router.put("/{user_id}", response_model=UserOut)
def update_role(user_id: int, data: UserUpdateRole, db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_service.update_role(db, user_id, data.role)

@router.delete("/{user_id}")
def remove_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    user_service.delete_user(db, user_id)
    return {"detail": "已删除"}
