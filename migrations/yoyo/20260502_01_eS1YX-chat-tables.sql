-- chat_tables
-- depends: 20260501_01_VEQxZ-scene-fts-index

CREATE TABLE "chat_thread" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "user_id" VARCHAR(36) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "story_id" VARCHAR(36) NOT NULL REFERENCES "story"("id") ON DELETE CASCADE,
    "title" VARCHAR(255) NOT NULL
);
CREATE INDEX "idx_chat_thread_user_id" ON "chat_thread" ("user_id");
CREATE INDEX "idx_chat_thread_story_id" ON "chat_thread" ("story_id");
CREATE INDEX "idx_chat_thread_story_updated" ON "chat_thread" ("story_id", "updated_at" DESC);


CREATE TABLE "chat_message" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "thread_id" VARCHAR(36) NOT NULL REFERENCES "chat_thread" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(36) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "role" VARCHAR(16) NOT NULL,
    "sequence" INTEGER NOT NULL,
    "content" TEXT NOT NULL,
    CHECK ("role" IN ('user', 'assistant', 'system', 'tool')),
    CHECK ("sequence" >= 0),
    CONSTRAINT "uid_chat_message_thread_sequence"
        UNIQUE ("thread_id", "sequence")
);
CREATE INDEX "idx_chat_message_thread_id" ON "chat_message" ("thread_id");
CREATE INDEX "idx_chat_message_user_id"   ON "chat_message" ("user_id");


CREATE TABLE "chat_tool_call" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "message_id" VARCHAR(36) NOT NULL REFERENCES "chat_message" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(36) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "tool_name" VARCHAR(64) NOT NULL,
    "sequence" INTEGER NOT NULL,
    "arguments" JSONB NOT NULL,
    "result" JSONB,
    "error" TEXT,
    CHECK ("sequence" >= 0),
    CONSTRAINT "uid_chat_tool_call_message_sequence" 
        UNIQUE ("message_id", "sequence")
);
CREATE INDEX "idx_chat_tool_call_message_id" ON "chat_tool_call" ("message_id");