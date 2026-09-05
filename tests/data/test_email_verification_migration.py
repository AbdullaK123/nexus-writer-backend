from pathlib import Path

import asyncpg


MIGRATION = Path(
    "migrations/yoyo/20260904_01_Dw7AU-add-email-verified-field.sql"
)


async def test_email_verification_migration_trusts_legacy_accounts_but_not_future_accounts(
    clean_db: asyncpg.Pool,
) -> None:
    """Exercise the migration itself inside a rolled-back DDL transaction.

    Existing users predate the verification feature and must remain trusted. New
    rows created after the migration must default to unverified.
    """
    migration_sql = MIGRATION.read_text()

    async with clean_db.acquire() as conn:
        transaction = conn.transaction()
        await transaction.start()
        try:
            await conn.execute('ALTER TABLE "user" DROP COLUMN email_verified')
            await conn.execute(
                """
                INSERT INTO "user" (
                    created_at, updated_at, id, username, email, password_hash, profile_img
                )
                VALUES (NOW(), NOW(), $1, $2, $3, $4, NULL)
                """,
                "legacy-user-id",
                "legacy-user",
                "legacy@example.com",
                "legacy-hash",
            )

            await conn.execute(migration_sql)

            assert await conn.fetchval(
                'SELECT email_verified FROM "user" WHERE id=$1',
                "legacy-user-id",
            ) is True

            await conn.execute(
                """
                INSERT INTO "user" (
                    created_at, updated_at, id, username, email, password_hash, profile_img
                )
                VALUES (NOW(), NOW(), $1, $2, $3, $4, NULL)
                """,
                "future-user-id",
                "future-user",
                "future@example.com",
                "future-hash",
            )

            assert await conn.fetchval(
                'SELECT email_verified FROM "user" WHERE id=$1',
                "future-user-id",
            ) is False
        finally:
            await transaction.rollback()
