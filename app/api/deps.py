from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role, role_at_least
from app.core.security import decode_token
from app.db.session import get_session
from app.models.user import User
from app.repositories.users import UsersRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if not sub:
            raise credentials_exception
        user_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    user = await UsersRepository(session).get(user_id)
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_role(min_role: Role):
    async def _check(user: User = Depends(get_current_user)) -> User:
        try:
            user_role = Role(user.role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")
        if not role_at_least(user_role, min_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _check

