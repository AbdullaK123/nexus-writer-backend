-- added auth tokens table
-- depends: 20260901_02_zf6ZP-make-pswd-hash-nullable
CREATE TABLE IF NOT EXISTS "auth_tokens" (
    "id" VARCHAR(36) PRIMARY KEY,
    "user_id" VARCHAR(255) NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
    "token_hash" TEXT NOT NULL UNIQUE,
    "purpose" TEXT NOT NULL CHECK (purpose IN ('email_verification', 'password_reset')),
    "expires_at" TIMESTAMPTZ NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);