-- added word count column to scene table
-- depends: 20260701_01_HXmH9-added-new-field-to-scene-table
ALTER TABLE scene ADD COLUMN IF NOT EXISTS word_count INT