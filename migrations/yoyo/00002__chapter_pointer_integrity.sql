-- Chapter pointer integrity. The doubly-linked list (prev_chapter_id /
-- next_chapter_id) is derived from story.path_array, but nothing at the DB
-- level has been preventing it from drifting into an invalid state. This
-- migration locks down four invariants:
--
--   1. A chapter cannot point to itself (prev/next ≠ id).
--   2. A pointer cannot cross stories — if A.next = B, then A.story_id =
--      B.story_id. Enforced via composite FK against (id, story_id).
--   3. At most one chapter may have any given chapter as its `next_chapter_id`
--      (and same for `prev_chapter_id`). This prevents two chapters claiming
--      the same successor — which would split the list.
--   4. The composite FKs SET NULL on the pointer column when the referenced
--      chapter is deleted (Postgres 15+ column-targeted SET NULL).
--
-- All FKs/uniques on the pointer columns are DEFERRABLE INITIALLY DEFERRED.
-- Reordering a chapter list with a single multi-row UPDATE temporarily holds
-- duplicate pointer values mid-statement; deferring the check to COMMIT lets
-- those bulk updates succeed.
--
-- NOTE: drops the pre-existing simple FKs on next_chapter_id / prev_chapter_id
-- so the stronger composite FKs can take their place. Names come from the
-- baseline migration emitted by Aerich.

-- ─── 1. drop old simple FKs on the pointer columns ──────────────────────────
ALTER TABLE "chapter"
    DROP CONSTRAINT IF EXISTS "chapter_next_chapter_id_fkey";
ALTER TABLE "chapter"
    DROP CONSTRAINT IF EXISTS "chapter_prev_chapter_id_fkey";

-- ─── 2. composite uniqueness on (id, story_id) so we can reference it ──────
-- Required as the target of a multi-column FK. id is already PK so this is
-- effectively a no-op for cardinality.
ALTER TABLE "chapter"
    ADD CONSTRAINT "uid_chapter_id_story_id" UNIQUE (id, story_id);

-- ─── 3. self-loop CHECKs ────────────────────────────────────────────────────
ALTER TABLE "chapter"
    ADD CONSTRAINT "chk_chapter_next_not_self"
    CHECK (next_chapter_id IS DISTINCT FROM id);
ALTER TABLE "chapter"
    ADD CONSTRAINT "chk_chapter_prev_not_self"
    CHECK (prev_chapter_id IS DISTINCT FROM id);

-- ─── 4. pointer uniqueness — one predecessor / one successor per chapter ───
-- NULLs are distinct under default Postgres semantics, so unattached chapters
-- (next/prev = NULL) are unaffected. Deferrable so bulk reorder UPDATEs can
-- swap pointer values within a single statement.
ALTER TABLE "chapter"
    ADD CONSTRAINT "uid_chapter_next_chapter_id" UNIQUE (next_chapter_id)
    DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "chapter"
    ADD CONSTRAINT "uid_chapter_prev_chapter_id" UNIQUE (prev_chapter_id)
    DEFERRABLE INITIALLY DEFERRED;

-- ─── 5. composite FKs — pointers must reference a chapter in the same story ─
-- Postgres 15+ column-targeted SET NULL: when the referenced chapter is
-- deleted, only the pointer column is nulled, never story_id.
ALTER TABLE "chapter"
    ADD CONSTRAINT "fk_chapter_next_same_story"
    FOREIGN KEY (next_chapter_id, story_id)
    REFERENCES "chapter" (id, story_id)
    ON DELETE SET NULL (next_chapter_id)
    DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "chapter"
    ADD CONSTRAINT "fk_chapter_prev_same_story"
    FOREIGN KEY (prev_chapter_id, story_id)
    REFERENCES "chapter" (id, story_id)
    ON DELETE SET NULL (prev_chapter_id)
    DEFERRABLE INITIALLY DEFERRED;
