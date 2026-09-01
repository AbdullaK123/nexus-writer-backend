from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic import EmailStr
from typing import Annotated, List, Literal, Optional
from datetime import datetime
import re
from src.data.schemas._base import ApiModel
from src.data.schemas.chapter import ChapterListItem
from src.infrastructure.config import config
from src.shared.text_types import PasswordInput, UserAgent, Username


class RegistrationData(ApiModel):
    username: Username
    email: EmailStr
    password: PasswordInput
    profile_img: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.match(config.auth.password_pattern, v):
            raise ValueError(
                "Password must be at least 8 characters and contain "
                "an uppercase letter, lowercase letter, digit, and special character"
            )
        return v


class AuthCredentials(ApiModel):
    email: EmailStr
    password: PasswordInput


class ConnectionDetails(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[UserAgent] = None


# ─── Repository row models ───────────────────────────────────────────────────
# Returned by UserRepository / SessionRepository. These replace direct use of
# the Tortoise model classes in the service layer.


class UserRow(BaseModel):
    """One row from the `user` table. Includes password_hash — do NOT return
    this to the API; convert to `UserResponse` first."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    password_hash: Optional[str]
    settings: dict
    profile_img: Optional[str]
    created_at: datetime
    updated_at: datetime

class OAuthUserRow(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    provider: str
    provider_user_id: str



class SessionRow(BaseModel):
    """One row from the `session` table."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    user_id: str
    expires_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    updated_at: datetime


class DashboardResponse(ApiModel):
    total_words: Optional[int] = Field(default=0)
    total_stories: Optional[int] = Field(default=0)
    chapters_total: Optional[int] = Field(default=0)
    chapters_published: Optional[int] = Field(default=0)
    scenes_tracked: Optional[int] = Field(default=0)
    streak_days: Optional[int] = Field(default=0)
    jump_back_in: Optional[List[ChapterListItem]] = []

class Notification(BaseModel):
    kind: Literal["scenes_extracted", "analysis_ready", "comments_ready", "job_failed"]
    story_id: str
    chapter_id: str
    message: str

class UserNavigationRow(ApiModel):
    chapter_id: str
    story_id: str
    chapter_number: int
    label: str

class StoryNavigationRow(ApiModel):
    story_id: str
    title: str

class UserNavigationResponse(ApiModel):
    links: List[UserNavigationRow]

class StoryNavigationResponse(ApiModel):
    links: List[StoryNavigationRow]


class AppearanceSettings(BaseModel):
    theme: Literal['system', 'light', 'dark'] = 'system'
    reduced_motion: bool = False


class EditorSettings(BaseModel):
    font_family: str = "Literata"
    font_size: int = 18
    line_height: float = 1.7
    content_width: int = 760
    spellcheck: bool = True

class NotificationSettings(BaseModel):
    analysis_ready: bool = True
    comments_ready: bool = True
    job_failures: bool = True


class AppearanceSettingsPayload(ApiModel):
    kind: Literal["appearance"]
    appearance: AppearanceSettings


class EditorSettingsPayload(ApiModel):
    kind: Literal["editor"]
    editor: EditorSettings


class NotificationSettingsPayload(ApiModel):
    kind: Literal["notifications"]
    notifications: NotificationSettings

SettingsPayload = Annotated[
    AppearanceSettingsPayload
    | EditorSettingsPayload
    | NotificationSettingsPayload,
    Field(discriminator="kind"),
]


class UserSettings(BaseModel):
    appearance: AppearanceSettings = Field(
        default_factory=lambda: AppearanceSettings()
    )
    editor: EditorSettings = Field(
        default_factory=EditorSettings
    )
    notifications: NotificationSettings = Field(
        default_factory=NotificationSettings
    )

class OAuthUserResponse(ApiModel):
    provider_id: str
    email: str
    name: str

class UserResponse(ApiModel):
    id: str
    username: str
    email: str
    profile_img: Optional[str]
    settings: UserSettings

    @classmethod
    def from_user_row(
        cls,
        user: UserRow
    ) -> "UserResponse":

        settings = UserSettings.model_validate(user.settings)

        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            profile_img=user.profile_img,
            settings = settings
        )