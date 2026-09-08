
from __future__ import annotations
from typing import Any

import asyncpg

from src.data.schemas.billing import SubscriptionRow
from src.data.schemas.enums import generate_uuid

_SUBSCRIPTION_COLUMNS = """
    id, user_id, stripe_subscription_id, status, price_id,
    current_period_start, current_period_end, cancel_at_period_end,
    created_at, updated_at
"""

Executor = Any


class SubscriptionRepository:

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool

    def _exe(self, executor: Executor | None) -> Executor:
        return executor if executor is not None else self._pool

    async def get_by_user_id(
        self,
        *,
        user_id: str,
        executor: Executor | None = None,
    ) -> SubscriptionRow | None:
        sql = f'SELECT {_SUBSCRIPTION_COLUMNS} FROM "subscription" WHERE user_id = $1'
        row = await self._exe(executor).fetchrow(sql, user_id)
        return SubscriptionRow.model_validate(dict(row)) if row else None

    async def upsert(
        self,
        *,
        user_id: str,
        stripe_subscription_id: str,
        status: str,
        price_id: str,
        current_period_start: int,
        current_period_end: int,
        cancel_at_period_end: bool,
        executor: Executor | None = None,
    ) -> SubscriptionRow:
        sql = f"""
            INSERT INTO "subscription"
                (id, user_id, stripe_subscription_id, status, price_id,
                 current_period_start, current_period_end, cancel_at_period_end,
                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5,
                    to_timestamp($6), to_timestamp($7), $8,
                    NOW(), NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                status = EXCLUDED.status,
                price_id = EXCLUDED.price_id,
                current_period_start = EXCLUDED.current_period_start,
                current_period_end = EXCLUDED.current_period_end,
                cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                updated_at = NOW()
            RETURNING {_SUBSCRIPTION_COLUMNS}
        """
        row = await self._exe(executor).fetchrow(
            sql,
            generate_uuid(),
            user_id,
            stripe_subscription_id,
            status,
            price_id,
            current_period_start,
            current_period_end,
            cancel_at_period_end,
        )
        assert row is not None, "subscription upsert must return the canonical entitlement row"
        return SubscriptionRow.model_validate(dict(row))

    async def delete_by_user_id(self, *, user_id: str, executor: Executor | None = None) -> None:
        await self._exe(executor).execute('DELETE FROM "subscription" WHERE user_id = $1', user_id)
