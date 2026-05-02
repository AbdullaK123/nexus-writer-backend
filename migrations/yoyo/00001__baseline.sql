-- Baseline schema. Idempotent: on existing DBs (managed by Aerich) this is a
-- no-op; on fresh DBs it creates everything.
--
-- Aerich and yoyo coexist during the migration off Tortoise. Once all
-- repositories are migrated, drop the aerich table and the migrations/models/
-- directory.

CREATE TABLE IF NOT EXISTS "user" (
    "created_at"    TIMESTAMPTZ  NOT NULL,
    "updated_at"    TIMESTAMPTZ  NOT NULL,
    "id"            VARCHAR(36)  NOT NULL PRIMARY KEY,
    "username"      VARCHAR(255) NOT NULL,
    "email"         VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "profile_img"   VARCHAR(512)
);
CREATE INDEX IF NOT EXISTS "idx_user_email_1b4f1c" ON "user" ("email");

CREATE TABLE IF NOT EXISTS "session" (
    "created_at" TIMESTAMPTZ  NOT NULL,
    "updated_at" TIMESTAMPTZ  NOT NULL,
    "session_id" VARCHAR(255) NOT NULL PRIMARY KEY,
    "expires_at" TIMESTAMPTZ  NOT NULL,
    "ip_address" VARCHAR(45),
    "user_agent" VARCHAR(512),
    "user_id"    VARCHAR(36)  NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_session_user_id_23ddbc" ON "session" ("user_id");

CREATE TABLE IF NOT EXISTS "story" (
    "created_at"    TIMESTAMPTZ  NOT NULL,
    "updated_at"    TIMESTAMPTZ  NOT NULL,
    "id"            VARCHAR(36)  NOT NULL PRIMARY KEY,
    "title"         VARCHAR(255) NOT NULL,
    "story_context" TEXT,
    "status"        VARCHAR(9)   NOT NULL,
    "path_array"    TEXT[],
    "user_id"       VARCHAR(36)  NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_story_user_id_8700fa" UNIQUE ("user_id", "title")
);
CREATE INDEX IF NOT EXISTS "idx_story_title_8888ab"   ON "story" ("title");
CREATE INDEX IF NOT EXISTS "idx_story_user_id_4d5372" ON "story" ("user_id");

CREATE TABLE IF NOT EXISTS "chapter" (
    "created_at"      TIMESTAMPTZ  NOT NULL,
    "updated_at"      TIMESTAMPTZ  NOT NULL,
    "id"              VARCHAR(36)  NOT NULL PRIMARY KEY,
    "title"           VARCHAR(255) NOT NULL,
    "content"         TEXT         NOT NULL,
    "published"       BOOL         NOT NULL,
    "word_count"      INT          NOT NULL,
    "next_chapter_id" VARCHAR(36)  REFERENCES "chapter" ("id") ON DELETE SET NULL,
    "prev_chapter_id" VARCHAR(36)  REFERENCES "chapter" ("id") ON DELETE SET NULL,
    "story_id"        VARCHAR(36)  NOT NULL REFERENCES "story" ("id") ON DELETE CASCADE,
    "user_id"         VARCHAR(36)  NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_chapter_user_id_887e2d" UNIQUE ("user_id", "story_id", "title")
);
CREATE INDEX IF NOT EXISTS "idx_chapter_story_i_1cbecd" ON "chapter" ("story_id");
CREATE INDEX IF NOT EXISTS "idx_chapter_user_id_819181" ON "chapter" ("user_id");

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
