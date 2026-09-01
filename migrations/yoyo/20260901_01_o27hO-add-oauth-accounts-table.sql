-- add oauth accounts table
-- depends: 20260830_02_wqEQo-story-chapter-scene-data-integrity

CREATE TABLE IF NOT EXISTS "oauth_accounts" (
    "id" VARCHAR(36) PRIMARY KEY,
    "user_id" VARCHAR(255) NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
    "provider" TEXT NOT NULL,
    "provider_user_id" TEXT NOT NULL,
    UNIQUE (provider, provider_user_id)
)