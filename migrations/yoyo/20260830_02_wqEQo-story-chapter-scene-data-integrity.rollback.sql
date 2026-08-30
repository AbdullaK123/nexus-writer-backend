-- Rollback for 20260830_02_wqEQo-story-chapter-scene-data-integrity.sql
--
-- Reverse the changes in the forward migration above.
ALTER TABLE "scene"
DROP CONSTRAINT "fk_scene_chapter_story_owner";

ALTER TABLE "chapter"
DROP CONSTRAINT "uid_chapter_id_story_user";

ALTER TABLE "chapter"
DROP CONSTRAINT "fk_chapter_story_owner";