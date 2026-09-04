-- add email verified field
-- depends: 20260902_01_vkQjf-added-auth-tokens-table

ALTER TABLE "user" ADD COLUMN "email_verified" BOOLEAN NOT NULL DEFAULT false;