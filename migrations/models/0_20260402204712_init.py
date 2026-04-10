from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "username" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "profile_img" VARCHAR(512) UNIQUE
);
CREATE INDEX IF NOT EXISTS "idx_user_email_1b4f1c" ON "user" ("email");
CREATE TABLE IF NOT EXISTS "session" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "session_id" VARCHAR(255) NOT NULL PRIMARY KEY,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "ip_address" VARCHAR(45),
    "user_agent" VARCHAR(512),
    "user_id" VARCHAR(36) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_session_user_id_23ddbc" ON "session" ("user_id");
CREATE TABLE IF NOT EXISTS "story" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "story_context" TEXT,
    "status" VARCHAR(9) NOT NULL DEFAULT 'Ongoing',
    "path_array" TEXT[],
    "user_id" VARCHAR(36) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_story_user_id_8700fa" UNIQUE ("user_id", "title")
);
CREATE INDEX IF NOT EXISTS "idx_story_title_8888ab" ON "story" ("title");
CREATE INDEX IF NOT EXISTS "idx_story_user_id_4d5372" ON "story" ("user_id");
COMMENT ON COLUMN "story"."status" IS 'COMPLETE: Complete\nON_HAITUS: On Hiatus\nONGOING: Ongoing';
CREATE TABLE IF NOT EXISTS "chapter" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "content" TEXT NOT NULL,
    "published" BOOL NOT NULL DEFAULT False,
    "word_count" INT NOT NULL DEFAULT 0,
    "last_extracted_word_count" INT,
    "condensed_context" TEXT,
    "timeline_context" TEXT,
    "emotional_arc" TEXT,
    "last_extracted_at" TIMESTAMPTZ,
    "extraction_version" VARCHAR(50),
    "next_chapter_id" VARCHAR(36) REFERENCES "chapter" ("id") ON DELETE SET NULL,
    "prev_chapter_id" VARCHAR(36) REFERENCES "chapter" ("id") ON DELETE SET NULL,
    "story_id" VARCHAR(36) NOT NULL REFERENCES "story" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(36) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_chapter_user_id_887e2d" UNIQUE ("user_id", "story_id", "title")
);
CREATE INDEX IF NOT EXISTS "idx_chapter_story_i_1cbecd" ON "chapter" ("story_id");
CREATE INDEX IF NOT EXISTS "idx_chapter_user_id_819181" ON "chapter" ("user_id");
CREATE TABLE IF NOT EXISTS "target" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "quota" INT NOT NULL DEFAULT 0,
    "frequency" VARCHAR(7) NOT NULL DEFAULT 'Daily',
    "from_date" TIMESTAMPTZ NOT NULL,
    "to_date" TIMESTAMPTZ NOT NULL,
    "story_id" VARCHAR(36) NOT NULL REFERENCES "story" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(36) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_target_story_i_cf0834" UNIQUE ("story_id", "frequency")
);
CREATE INDEX IF NOT EXISTS "idx_target_story_i_1aece3" ON "target" ("story_id");
CREATE INDEX IF NOT EXISTS "idx_target_user_id_c76581" ON "target" ("user_id");
COMMENT ON COLUMN "target"."frequency" IS 'DAILY: Daily\nWEEKLY: Weekly\nMONTHLY: Monthly';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "vO1S8vz38AODfjug=="
)
