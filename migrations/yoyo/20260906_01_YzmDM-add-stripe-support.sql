-- add stripe support
-- depends: 20260904_02_Qw8Lm-single-active-auth-token-per-purpose

ALTER TABLE "user" ADD COLUMN "stripe_customer_id" TEXT UNIQUE;

CREATE TABLE IF NOT EXISTS "subscription" (
    "id" VARCHAR(36) PRIMARY KEY,
    "user_id" VARCHAR(255) NOT NULL UNIQUE REFERENCES "user"("id") ON DELETE CASCADE,
    "stripe_subscription_id" TEXT NOT NULL UNIQUE,
    "status" TEXT NOT NULL CHECK (status IN (
        'active', 'past_due', 'canceled', 'incomplete',
        'incomplete_expired', 'trialing', 'unpaid', 'paused'
    )),
    "price_id" TEXT NOT NULL,
    "current_period_start" TIMESTAMPTZ NOT NULL,
    "current_period_end" TIMESTAMPTZ NOT NULL,
    "cancel_at_period_end" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);