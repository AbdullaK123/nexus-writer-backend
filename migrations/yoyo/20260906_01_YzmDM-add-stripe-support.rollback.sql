-- Rollback for 20260906_01_YzmDM-add-stripe-support.sql
--
-- Reverse the changes in the forward migration above.
DROP TABLE IF EXISTS "subscription";
ALTER TABLE "user" DROP COLUMN "stripe_customer_id";