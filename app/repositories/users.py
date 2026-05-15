from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return await self.session.scalar(stmt)

    async def create(self, *, email: str, hashed_password: str, full_name: str | None, role: str) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name, role=role, is_active=True)
        self.session.add(user)
        await self.session.flush()
        return user

