import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, Workspace

SECRET = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET_FOR_LOCAL_DEVELOPMENT_ONLY")
if os.getenv("APP_ENV") == "production" and SECRET.startswith("CHANGE_THIS"):
    raise RuntimeError("Set a long random JWT_SECRET before running in production")
ALGORITHM = "HS256"
EXPIRE = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return pwd.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd.verify(password, hashed)

def create_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE)
    return jwt.encode({"sub": str(user.id), "email": user.email, "exp": exp}, SECRET, algorithm=ALGORITHM)

def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(401, "Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(401, "Invalid or expired session")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(401, "Account not found")
    return user

def current_workspace(user: User = Depends(current_user), db: Session = Depends(get_db)) -> Workspace:
    workspace = db.query(Workspace).filter(Workspace.owner_id == user.id).first()
    if not workspace:
        raise HTTPException(404, "Workspace not found")
    return workspace
