from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .core.security import decode_token
from .db.postgres import get_db
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db_dep():
    yield from get_db()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db_dep)
) -> User:
    sub = decode_token(token)
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.email == sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
