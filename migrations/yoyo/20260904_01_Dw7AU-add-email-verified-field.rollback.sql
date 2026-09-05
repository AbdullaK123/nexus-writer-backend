-- Rollback for 20260904_01_Dw7AU-add-email-verified-field.sql
--
-- Reverse the changes in the forward migration above.
ALTER TABLE "user" DROP COLUMN "email_verified";