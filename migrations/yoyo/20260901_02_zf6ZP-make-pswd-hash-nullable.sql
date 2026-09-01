-- make_pswd_hash_nullable
-- depends: 20260901_01_o27hO-add-oauth-accounts-table

ALTER TABLE "user" ALTER COLUMN "password_hash" DROP NOT NULL