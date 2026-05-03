-- chat_tables
-- depends: 20260501_01_VEQxZ-scene-fts-index

-- chat_tool_call only exists if an older form of this migration was applied;
-- IF EXISTS keeps fresh rollbacks of the current schema clean.
DROP TABLE IF EXISTS "chat_tool_call";
DROP TABLE IF EXISTS "chat_message";
DROP TABLE IF EXISTS "chat_thread";