-- Rollback for 20260830_01_XmhnG-chat-table-data-integrity.sql
--
-- Reverse the changes in the forward migration above.

ALTER TABLE "chat_thread"
DROP CONSTRAINT "fk_chat_thread_story_owner";

ALTER TABLE "story"
DROP CONSTRAINT "uid_story_id_user_id";