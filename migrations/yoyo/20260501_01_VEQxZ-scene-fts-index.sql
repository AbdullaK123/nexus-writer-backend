-- scene_fts_index
-- depends: 00001__baseline  00002__chapter_pointer_integrity  00003__scene_table  00004__drop_aerich_table
--
-- Lexical half of hybrid scene search. Native Postgres FTS (tsvector + GIN)
-- so the schema works on any vanilla Postgres including Neon — pg_textsearch
-- (BM25) isn't available on managed providers.
--
-- Indexed expression is intentionally just title + description. Arrays
-- (tags, questions_raised) would force a wrapper to dodge array_to_string's
-- STABLE marking; not worth it. The vector half of the hybrid query already
-- covers those fields via the embedding input text.
--
-- The expression below MUST match the search query expression in
-- SceneRepository.search_scenes literally for the planner to use this index.

CREATE INDEX scene_fts_idx ON "scene"
USING GIN (
    to_tsvector(
        'english'::regconfig,
        coalesce(title, '') || ' ' || coalesce(description, '')
    )
);
