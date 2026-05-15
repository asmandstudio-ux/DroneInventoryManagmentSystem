from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.users import UsersRepository


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UsersRepository(session)
        self.session = session

    async def register(self, *, email: str, password: str, full_name: str | None, role: Role) -> str:
        existing = await self.users.get_by_email(email)
        if existing:
            raise AuthError("Email already registered")
        user = await self.users.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role.value,
        )
        await self.session.commit()
        return create_access_token(subject=str(user.id), role=user.role)

    async def login(self, *, email: str, password: str) -> str:
        user = await self.users.get_by_email(email)
        if not user or not user.is_active:
            raise AuthError("Invalid credentials")
        if not verify_password(password, user.hashed_password):
            raise AuthError("Invalid credentials")
        return create_access_token(subject=str(user.id), role=user.role)

