-- Recreate the Aerich history table. Empty — Aerich would not work with this
-- anyway because the model layer it tracked is deleted; this rollback exists
-- purely for symmetry with the forward migration.
CREATE TABLE IF NOT EXISTS "aerich" (
    "id"         SERIAL       NOT NULL PRIMARY KEY,
    "version"    VARCHAR(255) NOT NULL,
    "app"        VARCHAR(100) NOT NULL,
    "content"    JSONB        NOT NULL
);
