
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

    async def get_by_stripe_id(
        self,
        *,
        stripe_subscription_id: str,
        executor: Executor | None = None,
    ) -> SubscriptionRow | None:
        sql = f'SELECT {_SUBSCRIPTION_COLUMNS} FROM "subscription" WHERE stripe_subscription_id = $1'
        row = await self._exe(executor).fetchrow(sql, stripe_subscription_id)
        return SubscriptionRow.model_validate(dict(row)) if row else None

    async def create(
        self,
        *,
        user_id: str,
        stripe_subscription_id: str,
        status: str,
        price_id: str,
        current_period_start: int,
        current_period_end: int,
        executor: Executor | None = None,
    ) -> SubscriptionRow:
        sql = f"""
            INSERT INTO "subscription"
                (id, user_id, stripe_subscription_id, status, price_id,
                 current_period_start, current_period_end,
                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5,
                    to_timestamp($6), to_timestamp($7),
                    NOW(), NOW())
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
        )
        assert row is not None
        return SubscriptionRow.model_validate(dict(row))

    async def update_status(
        self,
        *,
        stripe_subscription_id: str,
        status: str,
        current_period_start: int,
        current_period_end: int,
        cancel_at_period_end: bool,
        executor: Executor | None = None,
    ) -> SubscriptionRow | None:
        sql = f"""
            UPDATE "subscription"
            SET status = $1,
                current_period_start = to_timestamp($2),
                current_period_end = to_timestamp($3),
                cancel_at_period_end = $4,
                updated_at = NOW()
            WHERE stripe_subscription_id = $5
            RETURNING {_SUBSCRIPTION_COLUMNS}
        """
        row = await self._exe(executor).fetchrow(
            sql,
            status,
            current_period_start,
            current_period_end,
            cancel_at_period_end,
            stripe_subscription_id,
        )
        return SubscriptionRow.model_validate(dict(row)) if row else None

    async def delete_by_stripe_id(
        self,
        *,
        stripe_subscription_id: str,
        executor: Executor | None = None,
    ) -> bool:
        sql = 'DELETE FROM "subscription" WHERE stripe_subscription_id = $1'
        status = await self._exe(executor).execute(sql, stripe_subscription_id)
        return not status.endswith(" 0")