-- Rollback for 20260902_01_vkQjf-added-auth-tokens-table.sql
--
-- Reverse the changes in the forward migration above.
DROP TABLE IF EXISTS "auth_tokens";