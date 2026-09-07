from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SubscriptionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    stripe_subscription_id: str
    status: str
    price_id: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime