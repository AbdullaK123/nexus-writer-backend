-- Rollback for 20260901_02_zf6ZP-make-pswd-hash-nullable.sql
--
-- Reverse the changes in the forward migration above.
ALTER TABLE "user" ALTER COLUMN "password_hash" SET NOT NULL