import pytest

from src.data.repositories.billing import SubscriptionRepository
from src.data.repositories.user import UserRepository
from tests.data.factories import make_user


async def test_deleted_user_lookup_returns_none_instead_of_crashing(clean_db):
    user = await make_user(clean_db)
    await clean_db.execute('DELETE FROM "user" WHERE id=$1', user.id)

    result = await UserRepository(clean_db).get_by_id(user.id)

    assert result is None, "a deleted account must reach the missing-user check instead of turning a stale session into a server error"


@pytest.mark.parametrize("status", [None, "canceled"])
async def test_user_lookup_preserves_customer_and_does_not_borrow_another_users_subscription(clean_db, status):
    user = await make_user(clean_db)
    other = await make_user(clean_db)
    users = UserRepository(clean_db)
    subscriptions = SubscriptionRepository(clean_db)
    await users.set_stripe_customer_id(user.id, "cus_existing")
    for account, account_status in [(other, "active"), (user, status)]:
        if account_status is not None:
            await subscriptions.upsert(
                user_id=account.id, stripe_subscription_id=f"sub_{account.id}",
                status=account_status, price_id="price_fake",
                current_period_start=100, current_period_end=200,
                cancel_at_period_end=False,
            )

    saved, subscription_status = await users.get_by_id(user.id)

    assert saved.id == user.id, "joining subscriptions must still select the requested account"
    assert saved.stripe_customer_id == "cus_existing", "losing the saved Stripe customer ID can create duplicate customer records during checkout"
    assert subscription_status == status, "another user's active subscription must never grant access to an unsubscribed or canceled account"
