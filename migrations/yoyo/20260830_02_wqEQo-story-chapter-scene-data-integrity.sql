-- story_chapter_scene_data_integrity
-- depends: 20260830_01_XmhnG-chat-table-data-integrity

-- A chapter's story_id and user_id must describe the SAME story.
ALTER TABLE "chapter"
ADD CONSTRAINT "fk_chapter_story_owner"
FOREIGN KEY ("story_id", "user_id")
REFERENCES "story" ("id", "user_id")
ON DELETE CASCADE;


-- Scene needs to reference this composite identity.
-- id is globally unique already, but PostgreSQL requires the exact
-- referenced column set to be UNIQUE for a composite FK.
ALTER TABLE "chapter"
ADD CONSTRAINT "uid_chapter_id_story_user"
UNIQUE ("id", "story_id", "user_id");


-- A scene's chapter_id, story_id and user_id must all describe
-- the SAME chapter.
ALTER TABLE "scene"
ADD CONSTRAINT "fk_scene_chapter_story_owner"
FOREIGN KEY ("chapter_id", "story_id", "user_id")
REFERENCES "chapter" ("id", "story_id", "user_id")
ON DELETE CASCADE;

