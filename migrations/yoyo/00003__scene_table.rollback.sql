-- Rollback scene table migration. Note: this does NOT restore extracted scene
-- data — it only restores the schema shape so a fresh re-extraction can run.
DROP TABLE IF EXISTS "scene";

ALTER TABLE "chapter" DROP COLUMN IF EXISTS "scenes_need_reextraction";
ALTER TABLE "chapter" DROP COLUMN IF EXISTS "scenes_extracted_at";

CREATE TABLE IF NOT EXISTS "extraction" (
    "created_at"         TIMESTAMPTZ NOT NULL,
    "updated_at"         TIMESTAMPTZ NOT NULL,
    "id"                 VARCHAR(36) NOT NULL PRIMARY KEY,
    "extraction_type"    VARCHAR(32) NOT NULL,
    "needs_reextraction" BOOL        NOT NULL,
    "data"               JSONB       NOT NULL,
    "chapter_id"         VARCHAR(36) NOT NULL REFERENCES "chapter" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_extraction_chapter_216c6d" UNIQUE ("chapter_id", "extraction_type")
);
CREATE INDEX IF NOT EXISTS "idx_extraction_needs_r_bca94e" ON "extraction" ("needs_reextraction");
CREATE INDEX IF NOT EXISTS "idx_extraction_chapter_d9d4f4" ON "extraction" ("chapter_id");

-- Note: vector extension not dropped — may be in use elsewhere.
