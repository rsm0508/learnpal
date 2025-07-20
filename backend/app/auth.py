from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.hash import bcrypt

from sqlmodel import Session, select
from .models import User, _engine
from .config import get_settings

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _session():
    with Session(_engine()) as s:
        yield s


def hash_pw(pw: str) -> str:
    return bcrypt.hash(pw)


def verify_pw(pw: str, pw_hash: str) -> bool:
    return bcrypt.verify(pw, pw_hash)


def create_token(user_id: int, tenant_id: int) -> str:
    cfg = get_settings()
    payload = {
        "sub": str(user_id),
        "tenant": tenant_id,
        "exp": datetime.utcnow() + timedelta(minutes=cfg.jwt_exp_minutes),
    }
    return jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)


def current_user(
    token: str = Depends(oauth_scheme), session: Session = Depends(_session)
) -> User:
    cfg = get_settings()
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid auth",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, cfg.jwt_secret, algorithms=[cfg.jwt_algorithm])
        user_id: str = payload.get("sub")
    except JWTError:
        raise cred_exc
    user = session.get(User, int(user_id))
    if not user:
        raise cred_exc
    return user
