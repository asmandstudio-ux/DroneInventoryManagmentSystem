from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pallet_check import PalletCheck, PalletReview


class PalletChecksRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, check_id: uuid.UUID) -> PalletCheck | None:
        return await self.session.get(PalletCheck, check_id)

    async def create(
        self,
        *,
        created_by_user_id: uuid.UUID,
        warehouse_id: uuid.UUID | None,
        location_code: str | None,
        overall: str | None,
        model_version: str | None,
        result: dict,
        evidence_object_key: str | None = None,
    ) -> PalletCheck:
        check = PalletCheck(
            created_by_user_id=created_by_user_id,
            warehouse_id=warehouse_id,
            location_code=location_code,
            overall=overall,
            model_version=model_version,
            result=result,
            evidence_object_key=evidence_object_key,
        )
        self.session.add(check)
        await self.session.flush()
        return check

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        warehouse_id: uuid.UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PalletCheck]:
        stmt: Select[tuple[PalletCheck]] = select(PalletCheck).where(
            PalletCheck.created_by_user_id == user_id
        )
        if warehouse_id is not None:
            stmt = stmt.where(PalletCheck.warehouse_id == warehouse_id)
        stmt = stmt.order_by(PalletCheck.created_at.desc()).limit(limit).offset(offset)
        rows = await self.session.scalars(stmt)
        return list(rows)

    async def add_review(
        self,
        *,
        check_id: uuid.UUID,
        reviewer_user_id: uuid.UUID,
        pallet_id: str | None,
        call: str | None,
        lines: dict | None,
    ) -> PalletReview:
        review = PalletReview(
            check_id=check_id,
            reviewer_user_id=reviewer_user_id,
            pallet_id=pallet_id,
            call=call,
            lines=lines,
        )
        self.session.add(review)
        await self.session.flush()
        return review

    async def list_reviews(self, *, check_id: uuid.UUID) -> list[PalletReview]:
        stmt = (
            select(PalletReview)
            .where(PalletReview.check_id == check_id)
            .order_by(PalletReview.created_at.asc())
        )
        rows = await self.session.scalars(stmt)
        return list(rows)
