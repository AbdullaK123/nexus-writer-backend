-- Replace the JSONB-blob `extraction` table with a real `scene` table:
-- one row per scene, with optional embedding columns the application fills
-- in asynchronously. Per-chapter staleness moves onto the `chapter` table.
--
-- Why:
--   * Scene-level granularity for vector search, filtering by tag/tension,
--     and joining against narrative metadata.
--   * Embeddings are first-class columns instead of buried in a JSON blob.
--   * `extraction.data` was a bag of JSON anyway — every read had to
--     deserialise the whole thing.

-- ─── 0. extension ──────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;

-- ─── 1. drop the old extraction table outright ─────────────────────────────
-- No data migration: extractions are derived from chapter content. The
-- background job will repopulate as chapters are touched.
DROP TABLE IF EXISTS "extraction";

-- ─── 2. per-chapter extraction status (was extraction.needs_reextraction) ──
ALTER TABLE "chapter"
    ADD COLUMN IF NOT EXISTS "scenes_need_reextraction" BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE "chapter"
    ADD COLUMN IF NOT EXISTS "scenes_extracted_at"      TIMESTAMPTZ;

-- Backfill: every existing chapter is "stale" so the worker re-extracts.
UPDATE "chapter" SET "scenes_need_reextraction" = TRUE WHERE "scenes_extracted_at" IS NULL;

CREATE INDEX IF NOT EXISTS "idx_chapter_scenes_stale"
    ON "chapter" ("scenes_need_reextraction")
    WHERE "scenes_need_reextraction" = TRUE;

-- ─── 3. scene table ────────────────────────────────────────────────────────
-- story_id and user_id are denormalised onto each scene so retrieval queries
-- (vector search across a story / a user's library) don't need to join up
-- through chapter every time. ON DELETE CASCADE keeps them consistent.
--
-- Embedding columns are nullable: the LLM extraction step writes everything
-- except the embedding, then a separate worker fills `embedding` /
-- `embedding_model` / `embedded_at` once it's been generated.
CREATE TABLE "scene" (
    "id"                 VARCHAR(36)  NOT NULL PRIMARY KEY,
    "chapter_id"         VARCHAR(36)  NOT NULL REFERENCES "chapter" ("id") ON DELETE CASCADE,
    "story_id"           VARCHAR(36)  NOT NULL REFERENCES "story"   ("id") ON DELETE CASCADE,
    "user_id"            VARCHAR(36)  NOT NULL REFERENCES "user"    ("id") ON DELETE CASCADE,
    "position"           INTEGER      NOT NULL,
    "title"              TEXT         NOT NULL,
    "start_quote"        TEXT         NOT NULL,
    "end_quote"          TEXT         NOT NULL,
    "description"        TEXT         NOT NULL,
    "tension"            VARCHAR(8)   NOT NULL,
    "pacing"             VARCHAR(8)   NOT NULL,
    "mentioned_entities" TEXT[]       NOT NULL DEFAULT '{}',
    "tags"               TEXT[]       NOT NULL DEFAULT '{}',
    "questions_raised"   TEXT[]       NOT NULL DEFAULT '{}',
    -- embedding columns; populated by the embedding worker, NULL until then
    "embedding"          vector(1536),
    "embedding_model"    VARCHAR(128),
    "embedded_at"        TIMESTAMPTZ,
    "created_at"         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    "updated_at"         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK ("tension" IN ('low', 'medium', 'high')),
    CHECK ("pacing"  IN ('slow', 'steady', 'fast')),
    CHECK ("position" >= 0),
    -- one scene per (chapter, position); enforces ordering uniqueness
    CONSTRAINT "uid_scene_chapter_position" UNIQUE ("chapter_id", "position")
);

CREATE INDEX "idx_scene_chapter_id" ON "scene" ("chapter_id");
CREATE INDEX "idx_scene_story_id"   ON "scene" ("story_id");
CREATE INDEX "idx_scene_user_id"    ON "scene" ("user_id");
-- Partial index for the embedding worker: "scenes still needing an embedding"
CREATE INDEX "idx_scene_pending_embedding"
    ON "scene" ("created_at")
    WHERE "embedding" IS NULL;
