-- Rollback for 20260716_01_qVZ7E-added-word-count-column-to-scene-table.sql
--
-- Reverse the changes in the forward migration above.
ALTER TABLE scene DROP COLUMN word_count