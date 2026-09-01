-- Rollback for 20260901_01_o27hO-add-oauth-accounts-table.sql
--
-- Reverse the changes in the forward migration above.
DROP TABLE IF EXISTS oauth_accounts;