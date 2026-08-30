-- chat_table_data_integrity
-- depends: 20260808_01_dIdE3-added-user-settings-column

ALTER TABLE "story"
ADD CONSTRAINT "uid_story_id_user_id"
UNIQUE ("id", "user_id");

ALTER TABLE "chat_thread"
ADD CONSTRAINT "fk_chat_thread_story_owner"
FOREIGN KEY ("story_id", "user_id")
REFERENCES "story" ("id", "user_id")
ON DELETE CASCADE;