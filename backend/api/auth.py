from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from services.auth_service import authenticate, register, create_token
from api.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/auth", tags=["认证"])

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, req.username, req.password)
    token = create_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, role=user.role, username=user.username)

@router.post("/register")
def register_user(req: RegisterRequest, _=Depends(require_admin), db: Session = Depends(get_db)):
    user = register(db, req.username, req.password, req.role)
    return {"id": user.id, "username": user.username, "role": user.role}
