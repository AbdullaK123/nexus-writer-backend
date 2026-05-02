ALTER TABLE "chapter"
    DROP CONSTRAINT IF EXISTS "fk_chapter_prev_same_story";
ALTER TABLE "chapter"
    DROP CONSTRAINT IF EXISTS "fk_chapter_next_same_story";
ALTER TABLE "chapter"
    DROP CONSTRAINT IF EXISTS "uid_chapter_prev_chapter_id";
ALTER TABLE "chapter"
    DROP CONSTRAINT IF EXISTS "uid_chapter_next_chapter_id";
ALTER TABLE "chapter"
    DROP CONSTRAINT IF EXISTS "chk_chapter_prev_not_self";
ALTER TABLE "chapter"
    DROP CONSTRAINT IF EXISTS "chk_chapter_next_not_self";
ALTER TABLE "chapter"
    DROP CONSTRAINT IF EXISTS "uid_chapter_id_story_id";

-- restore the simple FKs the baseline created
ALTER TABLE "chapter"
    ADD CONSTRAINT "chapter_next_chapter_id_fkey"
    FOREIGN KEY (next_chapter_id) REFERENCES "chapter" (id) ON DELETE SET NULL;
ALTER TABLE "chapter"
    ADD CONSTRAINT "chapter_prev_chapter_id_fkey"
    FOREIGN KEY (prev_chapter_id) REFERENCES "chapter" (id) ON DELETE SET NULL;
