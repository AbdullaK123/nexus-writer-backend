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
    "profile_img" VARCHAR(512)
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
    "next_chapter_id" VARCHAR(36) REFERENCES "chapter" ("id") ON DELETE SET NULL,
    "prev_chapter_id" VARCHAR(36) REFERENCES "chapter" ("id") ON DELETE SET NULL,
    "story_id" VARCHAR(36) NOT NULL REFERENCES "story" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(36) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_chapter_user_id_887e2d" UNIQUE ("user_id", "story_id", "title")
);
CREATE INDEX IF NOT EXISTS "idx_chapter_story_i_1cbecd" ON "chapter" ("story_id");
CREATE INDEX IF NOT EXISTS "idx_chapter_user_id_819181" ON "chapter" ("user_id");
CREATE TABLE IF NOT EXISTS "extraction" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "type" VARCHAR(20) NOT NULL,
    "is_stale" BOOL NOT NULL DEFAULT False,
    "prompt_version" INT NOT NULL DEFAULT 1,
    "data" JSONB NOT NULL,
    "story_id" VARCHAR(36) NOT NULL REFERENCES "story" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_extraction_story_i_f51459" UNIQUE ("story_id", "type")
);
CREATE INDEX IF NOT EXISTS "idx_extraction_story_i_53fabb" ON "extraction" ("story_id");
COMMENT ON COLUMN "extraction"."type" IS 'PLOT_THREAD: plot_thread\nCHARACTER: character\nWORLD_BIBLE: world_bible\nVOICE: voice';
CREATE TABLE IF NOT EXISTS "job" (
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "type" VARCHAR(20) NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'queued',
    "started_at" TIMESTAMPTZ,
    "queued_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completed_at" TIMESTAMPTZ,
    "failed_at" TIMESTAMPTZ,
    "message" VARCHAR(255) NOT NULL DEFAULT '',
    "params" JSONB NOT NULL,
    "story_id" VARCHAR(36) NOT NULL REFERENCES "story" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_job_story_i_8fb530" ON "job" ("story_id");
CREATE INDEX IF NOT EXISTS "idx_job_status_2b5fda" ON "job" ("status", "queued_at");
COMMENT ON COLUMN "job"."type" IS 'PLOT_THREAD: plot_thread\nCHARACTER: character\nWORLD_BIBLE: world_bible\nVOICE: voice';
COMMENT ON COLUMN "job"."status" IS 'QUEUED: queued\nSTARTED: started\nRUNNING: running\nCOMPLETED: completed\nFAILED: failed';
CREATE TABLE IF NOT EXISTS "summary" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "type" VARCHAR(20) NOT NULL,
    "is_stale" BOOL NOT NULL DEFAULT False,
    "prompt_version" INT NOT NULL DEFAULT 1,
    "content" TEXT NOT NULL,
    "chapter_id" VARCHAR(36) NOT NULL REFERENCES "chapter" ("id") ON DELETE CASCADE,
    "story_id" VARCHAR(36) NOT NULL REFERENCES "story" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_summary_story_i_829063" UNIQUE ("story_id", "chapter_id", "type")
);
CREATE INDEX IF NOT EXISTS "idx_summary_chapter_f3ddd0" ON "summary" ("chapter_id");
CREATE INDEX IF NOT EXISTS "idx_summary_story_i_ae8e5f" ON "summary" ("story_id");
COMMENT ON COLUMN "summary"."type" IS 'CHARACTER: character\nPLOT: plot\nWORLD: world\nSTYLE: style';
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
    "zYPP8ReBxx985v9qbnXndwq/M/vl5el/AFmwcQ=="
)
