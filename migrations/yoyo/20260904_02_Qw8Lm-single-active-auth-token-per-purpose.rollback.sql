-- rollback one active auth token per user and purpose

ALTER TABLE auth_tokens
DROP CONSTRAINT IF EXISTS auth_tokens_user_purpose_unique;
