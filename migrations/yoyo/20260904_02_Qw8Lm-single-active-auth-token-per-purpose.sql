-- keep exactly one active token per user and purpose
-- depends: 20260904_01_Dw7AU-add-email-verified-field

DELETE FROM auth_tokens older
USING auth_tokens newer
WHERE older.user_id = newer.user_id
  AND older.purpose = newer.purpose
  AND (
      older.created_at < newer.created_at
      OR (older.created_at = newer.created_at AND older.id < newer.id)
  );

ALTER TABLE auth_tokens
ADD CONSTRAINT auth_tokens_user_purpose_unique UNIQUE (user_id, purpose);
