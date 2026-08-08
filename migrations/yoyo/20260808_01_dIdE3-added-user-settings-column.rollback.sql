-- Rollback for 20260808_01_dIdE3-added-user-settings-column.sql
--
-- Reverse the changes in the forward migration above.
ALTER TABLE "user" DROP COLUMN settings;