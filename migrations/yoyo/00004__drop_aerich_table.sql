-- Phase 5 cleanup: Tortoise/Aerich are gone. The `aerich` migration-history
-- table is no longer touched by anything; yoyo tracks migrations in its own
-- `_yoyo_log` table. Drop it so `\dt` is no longer misleading.
DROP TABLE IF EXISTS "aerich";

