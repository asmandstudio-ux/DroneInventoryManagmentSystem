from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rbac import Role
from app.schemas.auth import RegisterRequest, Token
from app.schemas.user import UserOut
from app.services.auth_service import AuthError, AuthService
from app.db.session import get_session

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_session)) -> Token:
    # Safety default: only allow non-operator roles in dev.
    role = payload.role if settings.ENV.lower() == "dev" else Role.operator

    try:
        token = await AuthService(session).register(
            email=str(payload.email).lower(),
            password=payload.password,
            full_name=payload.full_name,
            role=role,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)
) -> Token:
    try:
        token = await AuthService(session).login(email=form_data.username.lower(), password=form_data.password)
    except AuthError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)

