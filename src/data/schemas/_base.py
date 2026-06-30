"""Shared base for API-facing Pydantic models.

Inherit from `ApiModel` for any schema that crosses the HTTP boundary
(request bodies, response models). Internal row models and LLM I/O
schemas should keep using plain `BaseModel` — they don't need camelCase
aliasing and the LLM ones MUST stay snake_case for prompt fidelity.

Behaviour added by this base:
  * camelCase JSON aliases via `to_camel`. FastAPI serializes responses
    by alias by default, so callers see `createdAt`, not `created_at`.
  * `populate_by_name=True` so Python construction stays snake_case
    (`Foo(created_at=...)` works) and request bodies accept either
    camelCase OR snake_case from the client.
  * `from_attributes=True` so we can validate straight from ORM /
    repository row objects without an explicit `.model_dump()`.
  * Datetime serialization normalised to ISO 8601 with a `Z` suffix
    when the value is UTC. Naive datetimes are assumed UTC and
    coerced — the alternative is silently emitting an ambiguous
    string the browser can't reliably parse.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer, AliasGenerator
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=None,       # Disables camelCase when reading data (DB rows)
            serialization_alias=to_camel, # Enables camelCase when producing API responses
        ),
        populate_by_name=True,
        from_attributes=True,
    )

    @field_serializer("*", when_used="json", check_fields=False)
    def _serialize_datetimes(self, value: Any) -> Any:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
            # 2026-05-06T14:23:00.123456Z — what the browser's Date()
            # constructor and Zod's z.coerce.date() / z.string().datetime()
            # both parse without help.
            return value.isoformat().replace("+00:00", "Z")
        return value
