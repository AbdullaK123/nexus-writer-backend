-- Rollback for 20260701_01_HXmH9-added-new-field-to-scene-table.sql
--
-- Reverse the changes in the forward migration above.
ALTER TABLE scene DROP COLUMN pov;