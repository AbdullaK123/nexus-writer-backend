-- added user settings column
-- depends: 20260716_01_qVZ7E-added-word-count-column-to-scene-table
ALTER TABLE "user"
ADD COLUMN IF NOT EXISTS settings JSONB NOT NULL DEFAULT '{}'::JSONB;
