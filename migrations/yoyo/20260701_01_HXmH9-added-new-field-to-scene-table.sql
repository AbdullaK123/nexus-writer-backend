-- added new field to scene table
-- depends: 20260502_01_eS1YX-chat-tables
ALTER TABLE scene ADD COLUMN IF NOT EXISTS pov VARCHAR(255) NOT NULL

