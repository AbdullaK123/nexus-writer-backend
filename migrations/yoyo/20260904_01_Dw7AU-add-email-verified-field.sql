-- add email verified field
-- depends: 20260902_01_vkQjf-added-auth-tokens-table

-- Accounts that existed before email verification shipped were already trusted by
-- the application. Backfill only those rows as verified, then make false the
-- default for every account created after this migration.
ALTER TABLE "user" ADD COLUMN "email_verified" BOOLEAN;
UPDATE "user" SET "email_verified" = TRUE;
ALTER TABLE "user" ALTER COLUMN "email_verified" SET DEFAULT FALSE;
ALTER TABLE "user" ALTER COLUMN "email_verified" SET NOT NULL;
