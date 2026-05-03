-- chat_tables
-- depends: 20260501_01_VEQxZ-scene-fts-index
--
-- Schema is pydantic-ai-native: each chat_message row stores one full
-- ModelMessage (a ModelRequest or ModelResponse) as JSONB, exactly the
-- shape produced by ModelMessagesTypeAdapter.dump_python(). This makes
-- replay trivial (fetch ordered rows -> validate_python -> pass to
-- agent.run(message_history=...)) and means tool calls / returns / text
-- parts all live inside the message JSON where pydantic-ai expects them.

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
    "id" VARCHAR(36) NOT NULL PRIMARY KEY,
    "thread_id" VARCHAR(36) NOT NULL REFERENCES "chat_thread" ("id") ON DELETE CASCADE,
    "user_id" VARCHAR(36) NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "sequence" INTEGER NOT NULL,
    -- Matches pydantic-ai's ModelMessage discriminator field.
    "kind" VARCHAR(16) NOT NULL,
    -- Full ModelMessage (ModelRequest or ModelResponse) serialized via
    -- ModelMessagesTypeAdapter. All parts (UserPromptPart, TextPart,
    -- ToolCallPart, ToolReturnPart, RetryPromptPart, ...) live inside.
    "message" JSONB NOT NULL,
    CHECK ("kind" IN ('request', 'response')),
    CHECK ("sequence" >= 0),
    CONSTRAINT "uid_chat_message_thread_sequence"
        UNIQUE ("thread_id", "sequence")
);
CREATE INDEX "idx_chat_message_thread_seq" ON "chat_message" ("thread_id", "sequence");
CREATE INDEX "idx_chat_message_user_id"    ON "chat_message" ("user_id");