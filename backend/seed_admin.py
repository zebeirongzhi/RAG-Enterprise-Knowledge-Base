"""创建初始管理员账号"""
from database import SessionLocal, engine, Base
from db_models.user import User
from services.auth_service import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

username = input("请输入管理员用户名: ").strip()
password = input("请输入管理员密码: ").strip()

if db.query(User).filter(User.username == username).first():
    print(f"用户 '{username}' 已存在")
else:
    user = User(
        username=username,
        password_hash=hash_password(password),
        role="admin"
    )
    db.add(user)
    db.commit()
    print(f"管理员 '{username}' 创建成功！")

db.close()
