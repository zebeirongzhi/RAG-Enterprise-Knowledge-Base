from sqlalchemy.orm import Session
from fastapi import HTTPException
from db_models.user import User
from services.auth_service import hash_password

def get_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()

def create_user(db: Session, username: str, password: str, role: str) -> User:
    if role not in ("admin", "customer"):
        raise HTTPException(status_code=400, detail="无效的角色")
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(username=username, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_role(db: Session, user_id: int, new_role: str) -> User:
    if new_role not in ("admin", "customer"):
        raise HTTPException(status_code=400, detail="无效的角色")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
