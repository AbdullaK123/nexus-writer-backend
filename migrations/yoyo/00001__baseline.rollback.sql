-- Rollback baseline. Drops everything in dependency order.
-- DO NOT RUN against a production DB unless you mean it.

DROP TABLE IF EXISTS "extraction";
DROP TABLE IF EXISTS "chapter";
DROP TABLE IF EXISTS "story";
DROP TABLE IF EXISTS "session";
DROP TABLE IF EXISTS "user";
